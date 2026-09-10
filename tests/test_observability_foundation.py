import io
import json
import logging
import unittest

from meylux.observability import HealthState, ObservabilityLimits, Severity, configure_logging, emit, get_context, new_correlation_id, scrub, set_context, clear_context


class ObservabilityFoundationTests(unittest.TestCase):
    def test_structured_event_shape_and_context(self):
        stream = io.StringIO()
        logger = configure_logging(stream=stream, logger_name="test.obs", limits=ObservabilityLimits(max_events_per_second=10))
        token = set_context(correlation_id="corr-1", task_order_id="TO-P1-007", execution_id="exec-1")
        try:
            emit(logger, Severity.INFO, "test.event", result="PASS")
        finally:
            clear_context(token)
        event = json.loads(stream.getvalue())
        self.assertEqual(event["event"], "test.event")
        self.assertEqual(event["severity"], "INFO")
        self.assertEqual(event["correlation_id"], "corr-1")
        self.assertEqual(event["task_order_id"], "TO-P1-007")
        self.assertEqual(event["result"], "PASS")

    def test_context_is_isolated_and_restored(self):
        token = set_context(correlation_id="outer", worker_id="w1")
        try:
            self.assertEqual(get_context()["correlation_id"], "outer")
            nested = set_context(correlation_id="inner")
            try:
                self.assertEqual(get_context()["correlation_id"], "inner")
            finally:
                clear_context(nested)
            self.assertEqual(get_context()["correlation_id"], "outer")
        finally:
            clear_context(token)
        self.assertEqual(get_context(), {})

    def test_secret_scrubbing_by_key_and_value(self):
        payload = {
            "password": "super-secret",
            "api_key": "AKIA-EXAMPLE",
            "nested": {"authorization": "Bearer abc.def.ghi"},
            "text": "-----BEGIN PRIVATE KEY-----\nSECRET\n-----END PRIVATE KEY-----",
            "safe": "visible",
        }
        cleaned = scrub(payload)
        self.assertEqual(cleaned["password"], "[REDACTED]")
        self.assertEqual(cleaned["api_key"], "[REDACTED]")
        self.assertEqual(cleaned["nested"]["authorization"], "[REDACTED]")
        self.assertEqual(cleaned["text"], "[REDACTED]")
        self.assertEqual(cleaned["safe"], "visible")

    def test_event_size_is_bounded(self):
        stream = io.StringIO()
        limits = ObservabilityLimits(max_event_bytes=300, max_string_length=10000, max_events_per_second=10)
        logger = configure_logging(stream=stream, logger_name="test.bound", limits=limits)
        emit(logger, Severity.ERROR, "oversized", payload="x" * 10000)
        self.assertLessEqual(len(stream.getvalue().encode()), 301)
        event = json.loads(stream.getvalue())
        self.assertTrue(event["observability_truncated"])

    def test_rate_limit_is_bounded(self):
        stream = io.StringIO()
        logger = configure_logging(stream=stream, logger_name="test.rate", limits=ObservabilityLimits(max_events_per_second=2))
        for _ in range(10):
            emit(logger, Severity.INFO, "rate.test")
        self.assertLessEqual(len(stream.getvalue().splitlines()), 2)

    def test_health_states_are_explicit(self):
        self.assertEqual(HealthState.NORMAL.value, "NORMAL")
        self.assertEqual(HealthState.OVERLOAD.value, "OVERLOAD")
        self.assertEqual(HealthState.DEPENDENCY_FAILURE.value, "DEPENDENCY_FAILURE")
        self.assertEqual(HealthState.UNAVAILABLE.value, "UNAVAILABLE")

    def test_correlation_id_is_unique_shape(self):
        first = new_correlation_id()
        second = new_correlation_id()
        self.assertNotEqual(first, second)
        self.assertEqual(len(first), 32)
        self.assertTrue(all(ch in "0123456789abcdef" for ch in first))


if __name__ == "__main__":
    unittest.main()
