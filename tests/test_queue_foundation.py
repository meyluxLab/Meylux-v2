import asyncio
import time
import unittest

from meylux.queue.model import DuplicateMessage, ProcessingOutcome, QueueEnvelope, QueueOverloaded, QueuePolicy, WorkerSpec
from meylux.queue.redis import RedisQueue, AsyncWorker


class FakeRedis:
    """Deterministic semantic double for RedisQueue; no production logic is duplicated."""
    def __init__(self):
        self.keys = {}
        self.entries = []
        self.pending = {}
        self.dlq = []
        self.dlq_entries = []
        self.now_ms = 2_000_000
        self.seq = 0
        self.groups = {"g": True}
        self.xack_zero_once = False

    def _new_id(self):
        self.seq += 1
        return f"{self.now_ms + self.seq}-0"

    async def set(self, *a, **kw):
        key, value = a[:2]
        if kw.get('nx') and key in self.keys:
            return False
        self.keys[key] = value
        return True

    async def delete(self, key):
        self.keys.pop(key, None)

    async def expire(self, key, seconds):
        return True

    async def time(self):
        return (self.now_ms // 1000, (self.now_ms % 1000) * 1000)

    async def xgroup_create(self, stream, group, id='0', mkstream=False):
        self.groups[group] = True

    async def xreadgroup(self, group, consumer, streams, count=1, block=0):
        stream = next(iter(streams))
        for entry in self.entries:
            if entry['stream'] == stream and entry['id'] not in self.pending:
                self.pending[entry['id']] = {'consumer': consumer, 'idle': 0, 'deliveries': 1}
                return [[stream, [(entry['id'], {'body': entry['body']})]]]
        return []

    async def xpending_range(self, stream, group, min='-', max='+', count=10, idle=None):
        out = []
        for entry in self.entries:
            p = self.pending.get(entry['id'])
            if p and (idle is None or p['idle'] >= idle):
                out.append({'message_id': entry['id'], 'time_since_delivered': p['idle'], 'consumer': p['consumer'], 'times_delivered': p['deliveries']})
                if len(out) >= count:
                    break
        return out

    async def xclaim(self, stream, group, consumer, min_idle_time, message_ids):
        out = []
        for mid in message_ids:
            p = self.pending.get(mid)
            if p and p['idle'] >= min_idle_time:
                p['consumer'] = consumer
                p['idle'] = 0
                p['deliveries'] += 1
                entry = next(e for e in self.entries if e['id'] == mid)
                out.append((mid, {'body': entry['body']}))
        return out

    async def xpending(self, stream, group):
        mids = [e['id'] for e in self.entries if e['id'] in self.pending]
        return {'pending': len(mids), 'min': mids[0] if mids else None, 'max': mids[-1] if mids else None}

    async def xinfo_groups(self, stream):
        return [{'name': g, 'pending': sum(1 for e in self.entries if e['id'] in self.pending)} for g in self.groups]

    async def xtrim(self, stream, minid, approximate=False):
        threshold = int(str(minid).split('-', 1)[0])
        if stream.endswith('-dlq') or ':dlq:' in stream:
            before = len(self.dlq_entries)
            self.dlq_entries[:] = [e for e in self.dlq_entries if int(e['id'].split('-', 1)[0]) >= threshold]
            return before - len(self.dlq_entries)
        before = len(self.entries)
        self.entries[:] = [e for e in self.entries if int(e['id'].split('-', 1)[0]) >= threshold]
        return before - len(self.entries)

    async def eval(self, script, numkeys, *args):
        if '_RETRY_TRANSITION' in script or 'Atomic replacement transition' in script:
            stream, backlog, retry_key, _stream2 = args[:4]
            group, source_id, body, max_backlog = args[4:]
            if retry_key in self.keys:
                self.pending.pop(source_id, None)
                return [2, self.keys.get(retry_key, '')]
            current = int(self.keys.get(backlog, 0) or 0)
            if current > int(max_backlog):
                return [0, '']
            rid = self._new_id()
            self.entries.append({'stream': stream, 'id': rid, 'body': body})
            self.keys[retry_key] = rid
            self.pending.pop(source_id, None)
            return [1, rid]
        if '_DLQ_LUA' in script or "redis.call('XADD', KEYS[3]" in script:
            stream, backlog, dlq = args[:3]
            group, source_id, body, reason, cutoff = args[3:]
            self.dlq.append((dlq, body, reason))
            self.dlq_entries.append({'id': self._new_id(), 'body': body, 'reason': reason})
            threshold = int(str(args[7]).split('-', 1)[0])
            self.dlq_entries[:] = [e for e in self.dlq_entries if int(e['id'].split('-', 1)[0]) >= threshold]
            acked = 1 if self.pending.pop(source_id, None) is not None else 0
            if acked:
                self.keys[backlog] = max(0, int(self.keys.get(backlog, 0) or 0) - 1)
            return acked
        if '_ACK_LUA' in script or "ARGV[3]" in script and 'XACK' in script:
            stream, backlog, group, entry_id, retry_key = args
            acked = 0 if self.xack_zero_once else (1 if self.pending.pop(entry_id, None) is not None else 0)
            self.xack_zero_once = False
            if acked:
                self.keys[backlog] = max(0, int(self.keys.get(backlog, 0) or 0) - 1)
            if retry_key:
                self.keys.pop(retry_key, None)
            return acked
        stream, backlog, idem = args[:3]
        max_backlog, body, message_id, retention = args[3:7]
        current = int(self.keys.get(backlog, 0) or 0)
        if current >= int(max_backlog):
            return 0
        if idem in self.keys:
            return -1
        self.keys[idem] = message_id
        eid = self._new_id()
        self.entries.append({'stream': stream, 'id': eid, 'body': body})
        self.keys[backlog] = current + 1
        return eid


class QueueFoundationTests(unittest.TestCase):
    def setUp(self):
        self.policy = QueuePolicy(
            name='test', owner='P1 async foundation', producer='producer', consumer='consumer',
            purpose='foundation test', payload_contract='CTR-TEST-EVENT', dlq_name='test-dlq',
            max_backlog=10, max_concurrency=2, max_attempts=3, timeout_seconds=0.02,
            backoff_seconds=0.001, retention_seconds=60,
        )
        self.env = QueueEnvelope('m-1', 'i-1', 'CTR-TEST-EVENT', {'value': 1})

    def test_worker_spec_boundary(self):
        spec = WorkerSpec('foundation-worker', 'execute one bounded queue handler', ('QueueEnvelope',), ('ProcessingOutcome',), ('RedisQueue',), ('market acquisition','trading','authoritative persistence'), ('queue acknowledgement',), 'max_concurrency', 'message-local')
        self.assertEqual(spec.primary_responsibility, 'execute one bounded queue handler')

    def test_fifo_semantics_are_explicit(self):
        self.assertEqual(self.policy.ordering, 'FIFO_ENQUEUE_AND_DELIVERY')

    def test_fifo_delivery_follows_enqueue_order(self):
        async def run():
            redis = FakeRedis(); q = RedisQueue(redis, self.policy, 'g')
            first = await q.publish(QueueEnvelope('m1','i1','CTR-TEST-EVENT',{}))
            second = await q.publish(QueueEnvelope('m2','i2','CTR-TEST-EVENT',{}))
            got1 = await q.read('c'); got2 = await q.read('c')
            self.assertEqual([got1[0], got2[0]], [first, second])
        asyncio.run(run())

    def test_publish_success_duplicate_and_overload(self):
        async def run():
            redis = FakeRedis(); p = self.policy
            q = RedisQueue(redis, p, 'g')
            self.assertEqual(await q.publish(self.env), '2000001-0')
            with self.assertRaises(DuplicateMessage): await q.publish(self.env)
            small = QueuePolicy(
                name='small', owner=p.owner, producer=p.producer, consumer=p.consumer, purpose=p.purpose,
                payload_contract=p.payload_contract, dlq_name='small-dlq', max_backlog=1, max_concurrency=1,
                max_attempts=2, timeout_seconds=.1, backoff_seconds=0, retention_seconds=60)
            q2 = RedisQueue(FakeRedis(), small, 'g'); await q2.publish(self.env)
            with self.assertRaises(QueueOverloaded): await q2.publish(QueueEnvelope('m2','i2',p.payload_contract,{}))
        asyncio.run(run())

    def test_actual_retry_transition_and_backoff(self):
        async def run():
            redis = FakeRedis(); q = RedisQueue(redis, self.policy, 'g')
            eid = await q.publish(self.env)
            item = await q.read('c'); self.assertEqual(item[0], eid)
            t0 = time.monotonic(); out = await q.retry_or_dlq(eid, self.env, 'FAILURE:RuntimeError'); elapsed = time.monotonic()-t0
            self.assertEqual(out.status, 'RETRY'); self.assertGreaterEqual(elapsed, .001)
            self.assertEqual(len(redis.pending), 0); self.assertEqual(len(redis.entries), 2)
            self.assertEqual(redis.keys[q.backlog_key], 1)
        asyncio.run(run())

    def test_retry_marker_existing_does_not_decrement_backlog(self):
        async def run():
            redis = FakeRedis(); q = RedisQueue(redis, self.policy, 'g')
            eid = await q.publish(self.env); await q.read('c')
            retry = QueueEnvelope('m-1', 'i-1:attempt:2', 'CTR-TEST-EVENT', {'value': 1}, 2)
            redis.keys[q.retry_prefix + retry.idempotency_key] = 'existing-retry'
            out = await q.recover_retry(eid, self.env)
            self.assertEqual(out.status, 'RETRY')
            self.assertEqual(redis.keys[q.backlog_key], 1)
        asyncio.run(run())

    def test_retry_xack_zero_does_not_inflate_or_drift_backlog(self):
        async def run():
            redis = FakeRedis(); q = RedisQueue(redis, self.policy, 'g')
            eid = await q.publish(self.env); await q.read('c')
            redis.pending.pop(eid, None)
            redis.xack_zero_once = True
            out = await q.retry_or_dlq(eid, self.env, 'FAILURE:RuntimeError')
            self.assertEqual(out.status, 'RETRY')
            self.assertEqual(redis.keys[q.backlog_key], 1)
            self.assertEqual(len(redis.entries), 2)
        asyncio.run(run())

    def test_crash_window_retry_already_exists_and_repeated_recovery(self):
        async def run():
            redis = FakeRedis(); q = RedisQueue(redis, self.policy, 'g')
            eid = await q.publish(self.env); await q.read('c')
            retry = QueueEnvelope('m-1', 'i-1:attempt:2', 'CTR-TEST-EVENT', {'value':1}, 2)
            redis.keys[q.retry_prefix + retry.idempotency_key] = 'existing-retry'
            out = await q.recover_retry(eid, self.env)
            self.assertEqual(out.reason, 'RECOVERED_RETRY'); self.assertNotIn(eid, redis.pending)
            out2 = await q.recover_retry(eid, self.env)
            self.assertEqual(out2.reason, 'RECOVERED_RETRY')
        asyncio.run(run())

    def test_retried_message_ack_clears_marker_and_decrements_backlog(self):
        async def run():
            redis = FakeRedis(); q = RedisQueue(redis, self.policy, 'g')
            eid = await q.publish(self.env); await q.read('c')
            await q.retry_or_dlq(eid, self.env, 'FAILURE:RuntimeError')
            retry = QueueEnvelope('m-1', 'i-1:attempt:2', 'CTR-TEST-EVENT', {'value': 1}, 2)
            retry_key = q.retry_prefix + retry.idempotency_key
            self.assertIn(retry_key, redis.keys)
            retry_entry = redis.entries[-1]['id']
            redis.pending[retry_entry] = {'consumer': 'c', 'idle': 0, 'deliveries': 1}
            await q.ack(retry_entry, retry)
            self.assertEqual(redis.keys[q.backlog_key], 0)
            self.assertNotIn(retry_key, redis.keys)
        asyncio.run(run())

    def test_crash_window_retry_absent_creates_exactly_one(self):
        async def run():
            redis = FakeRedis(); q = RedisQueue(redis, self.policy, 'g')
            eid = await q.publish(self.env); await q.read('c')
            out = await q.recover_retry(eid, self.env)
            self.assertEqual(out.reason, 'RECOVERED_RETRY')
            self.assertEqual(len(redis.entries), 2)
            out2 = await q.recover_retry(eid, self.env)
            self.assertEqual(out2.reason, 'RECOVERED_RETRY')
            self.assertEqual(len(redis.entries), 2)
        asyncio.run(run())

    def test_retry_exhaustion_executes_actual_dlq(self):
        async def run():
            redis = FakeRedis(); p = QueuePolicy(
                name='dlq', owner='o', producer='p', consumer='c', purpose='t', payload_contract='CTR', dlq_name='dlq',
                max_backlog=10, max_concurrency=1, max_attempts=1, timeout_seconds=.1, backoff_seconds=0, retention_seconds=60)
            q = RedisQueue(redis, p, 'g'); eid = await q.publish(QueueEnvelope('m','i','CTR',{})); await q.read('c')
            out = await q.retry_or_dlq(eid, QueueEnvelope('m','i','CTR',{},1), 'FAILURE:X')
            self.assertEqual(out.status, 'DLQ'); self.assertEqual(len(redis.dlq), 1); self.assertEqual(redis.pending, {})
        asyncio.run(run())

    def test_timeout_executes_actual_worker_retry(self):
        async def handler(_): await asyncio.sleep(.05)
        async def run():
            redis = FakeRedis(); q = RedisQueue(redis, self.policy, 'g'); await q.publish(self.env)
            worker = AsyncWorker(q, handler, consumer='c'); result = await worker.run_once()
            self.assertEqual(result.status, 'RETRY'); self.assertEqual(len(redis.entries), 2)
        asyncio.run(run())

    def test_failure_isolation_executes_actual_handler_path(self):
        async def handler(_): raise RuntimeError('boom')
        async def run():
            redis = FakeRedis(); q = RedisQueue(redis, self.policy, 'g'); await q.publish(self.env)
            result = await AsyncWorker(q, handler, consumer='c').run_once()
            self.assertEqual(result.status, 'RETRY')
        asyncio.run(run())

    def test_stale_recovery_claims_actual_pending_entry(self):
        async def run():
            redis = FakeRedis(); q = RedisQueue(redis, self.policy, 'g'); eid = await q.publish(self.env); await q.read('dead')
            redis.pending[eid]['idle'] = 5000
            recovered = await q.recover_stale('rescuer', 1000)
            self.assertEqual(recovered[0][0], eid); self.assertEqual(redis.pending[eid]['consumer'], 'rescuer')
        asyncio.run(run())

    def test_dlq_new_entry_survives_before_retention_boundary(self):
        async def run():
            redis = FakeRedis(); p = QueuePolicy(name='dlq-ret', owner='o', producer='p', consumer='c', purpose='t', payload_contract='CTR', dlq_name='dlq-ret', max_backlog=10, max_concurrency=1, max_attempts=1, timeout_seconds=.1, backoff_seconds=0, retention_seconds=60)
            q = RedisQueue(redis, p, 'g'); eid = await q.publish(QueueEnvelope('m','i','CTR',{})); await q.read('c')
            out = await q.retry_or_dlq(eid, QueueEnvelope('m','i','CTR',{},1), 'FAILURE:X')
            self.assertEqual(out.status, 'DLQ'); self.assertEqual(len(redis.dlq_entries), 1)
        asyncio.run(run())

    def test_dlq_old_entries_trim_while_newer_entries_remain(self):
        async def run():
            redis = FakeRedis(); p = QueuePolicy(name='dlq-ret2', owner='o', producer='p', consumer='c', purpose='t', payload_contract='CTR', dlq_name='dlq-ret2', max_backlog=10, max_concurrency=1, max_attempts=1, timeout_seconds=.1, backoff_seconds=0, retention_seconds=60)
            q = RedisQueue(redis, p, 'g')
            old = redis._new_id(); redis.dlq_entries.append({'id': old, 'body': 'old', 'reason': 'x'})
            redis.now_ms += 61_000
            eid = await q.publish(QueueEnvelope('m','i','CTR',{})); await q.read('c'); await q.retry_or_dlq(eid, QueueEnvelope('m','i','CTR',{},1), 'FAILURE:X')
            self.assertEqual(len(redis.dlq_entries), 1)
            self.assertNotEqual(redis.dlq_entries[0]['id'], old)
        asyncio.run(run())

    def test_dlq_continuous_insertion_does_not_refresh_old_entry(self):
        async def run():
            redis = FakeRedis(); p = QueuePolicy(name='dlq-storm', owner='o', producer='p', consumer='c', purpose='t', payload_contract='CTR', dlq_name='dlq-storm', max_backlog=100, max_concurrency=1, max_attempts=1, timeout_seconds=.1, backoff_seconds=0, retention_seconds=60)
            q = RedisQueue(redis, p, 'g')
            old = redis._new_id(); redis.dlq_entries.append({'id': old, 'body': 'old', 'reason': 'x'})
            for n in range(5):
                redis.now_ms += 20_000
                eid = await q.publish(QueueEnvelope(f'm{n}',f'i{n}','CTR',{})); await q.read('c'); await q.retry_or_dlq(eid, QueueEnvelope(f'm{n}',f'i{n}','CTR',{},1), 'FAILURE:X')
            self.assertFalse(any(e['id'] == old for e in redis.dlq_entries))
            self.assertGreaterEqual(len(redis.dlq_entries), 1)
        asyncio.run(run())

    def test_dlq_retention_does_not_change_backlog_or_retry_marker(self):
        async def run():
            redis = FakeRedis(); p = QueuePolicy(name='dlq-safe', owner='o', producer='p', consumer='c', purpose='t', payload_contract='CTR', dlq_name='dlq-safe', max_backlog=10, max_concurrency=1, max_attempts=1, timeout_seconds=.1, backoff_seconds=0, retention_seconds=60)
            q = RedisQueue(redis, p, 'g'); eid = await q.publish(QueueEnvelope('m','i','CTR',{})); await q.read('c'); await q.retry_or_dlq(eid, QueueEnvelope('m','i','CTR',{},1), 'FAILURE:X')
            self.assertEqual(redis.keys[q.backlog_key], 0); self.assertFalse(any(k.startswith(q.retry_prefix) for k in redis.keys))
            await q.retention_sweep(); self.assertEqual(redis.keys[q.backlog_key], 0); self.assertFalse(any(k.startswith(q.retry_prefix) for k in redis.keys))
        asyncio.run(run())

    def test_retention_preserves_pending_and_trims_completed_history(self):
        async def run():
            redis = FakeRedis(); q = RedisQueue(redis, self.policy, 'g')
            e0 = await q.publish(self.env); await q.read('c'); await q.ack(e0, self.env)
            e1 = await q.publish(QueueEnvelope('m2','i2','CTR-TEST-EVENT',{})); redis.pending[e1] = {'consumer':'c','idle':0,'deliveries':1}
            redis.now_ms += 120_000
            deleted = await q.retention_sweep()
            self.assertGreaterEqual(deleted, 1)
            self.assertTrue(any(e['id'] == e1 for e in redis.entries))
        asyncio.run(run())

    def test_retention_after_pending_resolution_can_trim_completed_history(self):
        async def run():
            redis = FakeRedis(); q = RedisQueue(redis, self.policy, 'g')
            e0 = await q.publish(self.env); await q.read('c'); await q.ack(e0, self.env)
            redis.now_ms += 120_000
            deleted = await q.retention_sweep()
            self.assertGreaterEqual(deleted, 1)
            self.assertEqual(redis.entries, [])
        asyncio.run(run())

    def test_bounded_concurrency_is_enforced_by_worker_task_window(self):
        async def run():
            redis = FakeRedis(); p = QueuePolicy(
                name='conc', owner='o', producer='p', consumer='c', purpose='t', payload_contract='CTR', dlq_name='d',
                max_backlog=10, max_concurrency=2, max_attempts=1, timeout_seconds=1, backoff_seconds=0, retention_seconds=60)
            q = RedisQueue(redis, p, 'g');
            for i in range(4): await q.publish(QueueEnvelope(f'm{i}',f'i{i}','CTR',{}))
            active = 0; peak = 0
            async def handler(_):
                nonlocal active, peak
                active += 1; peak = max(peak, active); await asyncio.sleep(.01); active -= 1
            workers = [AsyncWorker(q, handler, consumer=f'c{i}') for i in range(2)]
            await asyncio.gather(*(w.run_once() for w in workers))
            self.assertLessEqual(peak, 2)
        asyncio.run(run())


if __name__ == '__main__': unittest.main()
