from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "docs/registry/contracts.yaml"


class ContractRegistryTests(unittest.TestCase):
    def test_canonical_candle_registry_record_exists(self):
        text = REGISTRY.read_text(encoding="utf-8")
        self.assertIn("sid: CTR-V2-CANONICAL-CANDLE", text)
        self.assertIn("lifecycle_status: IMPLEMENTED / SELF-TESTED", text)

    def test_registry_remains_secret_free(self):
        text = REGISTRY.read_text(encoding="utf-8")
        for marker in ("password", "token", "api_key", "secret"):
            self.assertNotIn(marker, text.lower())


if __name__ == "__main__":
    unittest.main()
