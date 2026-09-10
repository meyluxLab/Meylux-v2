from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "docs/registry/contracts.yaml"


class ContractRegistryTests(unittest.TestCase):
    def setUp(self):
        self.registry = REGISTRY

    def test_required_canonical_contract_registry_records_exist(self):
        text = self.registry.read_text()
        for sid in (
            "CTR-V2-CANONICAL-CANDLE",
            "CTR-V2-CANONICAL-INSTRUMENT",
            "CTR-V2-CANONICAL-TRADE",
            "CTR-V2-CANONICAL-ORDERBOOK",
            "CTR-V2-CANONICAL-DERIVATIVES",
        ):
            self.assertIn(f"sid: {sid}", text)
            self.assertIn("lifecycle_status: IMPLEMENTED / SELF-TESTED", text)

    def test_registry_remains_secret_free(self):
        text = self.registry.read_text().lower()
        for marker in ("password", "secret", "api_key", "private_key", "access_token"):
            self.assertNotIn(marker, text)


if __name__ == "__main__":
    unittest.main()
