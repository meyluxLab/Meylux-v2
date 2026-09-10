import io, json, unittest
from unittest.mock import patch
from meylux.observability import classify_health, HealthState, ObservabilityLimits, Severity, clear_context, configure_logging, emit, get_context, new_correlation_id, scrub, set_context
class ObservabilityFoundationTests(unittest.TestCase):
 def test_structured_event_and_context(self):
  out=io.StringIO(); log=configure_logging(stream=out,logger_name="t.obs",limits=ObservabilityLimits(max_events_per_second=10)); tok=set_context(correlation_id="corr-1",task_order_id="TO-P1-007")
  try: emit(log,Severity.INFO,"test.event",result="PASS")
  finally: clear_context(tok)
  e=json.loads(out.getvalue()); self.assertEqual(e["event"],"test.event"); self.assertEqual(e["severity"],"INFO"); self.assertEqual(e["correlation_id"],"corr-1"); self.assertEqual(e["task_order_id"],"TO-P1-007")
 def test_context_restores(self):
  tok=set_context(correlation_id="outer")
  try:
   inner=set_context(correlation_id="inner"); clear_context(inner); self.assertEqual(get_context()["correlation_id"],"outer")
  finally: clear_context(tok)
  self.assertEqual(get_context(),{})
 def test_secret_scrubbing(self):
  e=scrub({"password":"x","api_key":"y","nested":{"authorization":"Bearer abc.def"},"safe":"visible"}); self.assertEqual(e["password"],"[REDACTED]"); self.assertEqual(e["api_key"],"[REDACTED]"); self.assertEqual(e["nested"]["authorization"],"[REDACTED]"); self.assertEqual(e["safe"],"visible")
 def test_bounded_size(self):
  out=io.StringIO(); log=configure_logging(stream=out,logger_name="t.bound",limits=ObservabilityLimits(max_event_bytes=300,max_string_length=10000,max_events_per_second=10)); emit(log,Severity.ERROR,"oversized",payload="x"*10000); self.assertLessEqual(len(out.getvalue().encode()),301); self.assertTrue(json.loads(out.getvalue())["observability_truncated"])
 def test_rate_bound(self):
  out=io.StringIO(); log=configure_logging(stream=out,logger_name="t.rate",limits=ObservabilityLimits(max_events_per_second=2)); [emit(log,Severity.INFO,"rate.test") for _ in range(10)]; self.assertLessEqual(len(out.getvalue().splitlines()),2)
 def test_critical_events_bypass_rate_saturation(self):
  out=io.StringIO(); log=configure_logging(stream=out,logger_name="t.rate.critical",limits=ObservabilityLimits(max_events_per_second=2))
  [emit(log,Severity.INFO,"rate.test") for _ in range(10)]
  emit(log,Severity.ERROR,"critical.error")
  emit(log,Severity.CRITICAL,"critical.event")
  events=[json.loads(line) for line in out.getvalue().splitlines()]
  self.assertLessEqual(sum(e["severity"] == "INFO" for e in events),2)
  self.assertTrue(any(e["event"] == "critical.error" and e["severity"] == "ERROR" for e in events))
  self.assertTrue(any(e["event"] == "critical.event" and e["severity"] == "CRITICAL" for e in events))

 def test_error_and_critical_events_remain_bounded_under_stress(self):
  out=io.StringIO(); limit=1; log=configure_logging(stream=out,logger_name="t.rate.stress",limits=ObservabilityLimits(max_events_per_second=limit))
  # Hold the production rate-limit window at one deterministic second.
  # Production behavior remains based on the real wall clock; this patch is
  # test-only and removes host-speed dependence from the saturation boundary.
  with patch("meylux.observability.core.time.time", return_value=1234567890.25):
   [emit(log,Severity.INFO,"info.stress") for _ in range(10000)]
   [emit(log,Severity.ERROR,"error.stress") for _ in range(10000)]
   [emit(log,Severity.CRITICAL,"critical.stress") for _ in range(10000)]
  events=[json.loads(line) for line in out.getvalue().splitlines()]
  self.assertEqual(sum(e["severity"] == "INFO" for e in events),1)
  self.assertEqual(sum(e["severity"] == "ERROR" for e in events),1)
  self.assertEqual(sum(e["severity"] == "CRITICAL" for e in events),1)
  self.assertEqual(len(events),limit+2)

 def test_rate_filter_has_no_unbounded_buffer(self):
  out=io.StringIO(); log=configure_logging(stream=out,logger_name="t.rate.bound",limits=ObservabilityLimits(max_events_per_second=1))
  [emit(log,Severity.INFO,"rate.test") for _ in range(1000)]
  rate_filter=next(f for f in log.handlers[0].filters if f.__class__.__name__ == "_RateFilter")
  self.assertEqual(set(rate_filter.__dict__), {"limit", "second", "count", "error_count", "critical_count"})
  self.assertLessEqual(rate_filter.count, rate_filter.limit)
  self.assertLessEqual(rate_filter.error_count,1)
  self.assertLessEqual(rate_filter.critical_count,1)
  self.assertLessEqual(len(out.getvalue().splitlines()),1)

 def test_severity_mapping(self):
  out=io.StringIO(); log=configure_logging(stream=out,logger_name="t.severity",limits=ObservabilityLimits(max_events_per_second=10)); emit(log,Severity.ERROR,"error.event"); self.assertEqual(json.loads(out.getvalue())["severity"],"ERROR")
 def test_health_classification_is_deterministic(self):
  self.assertEqual(classify_health(backlog=0,max_backlog=10),HealthState.NORMAL)
  self.assertEqual(classify_health(backlog=8,max_backlog=10),HealthState.DEGRADED)
  self.assertEqual(classify_health(backlog=10,max_backlog=10),HealthState.OVERLOAD)
  self.assertEqual(classify_health(backlog=1,max_backlog=10,dependency_available=False),HealthState.DEPENDENCY_FAILURE)
  self.assertEqual(classify_health(backlog=1,max_backlog=10,capability_available=False),HealthState.UNAVAILABLE)
 def test_health_states(self): self.assertEqual({x.value for x in HealthState},{"NORMAL","DEGRADED","OVERLOAD","DEPENDENCY_FAILURE","UNAVAILABLE"})
 def test_correlation_id(self): self.assertNotEqual(new_correlation_id(),new_correlation_id())
if __name__=="__main__": unittest.main()