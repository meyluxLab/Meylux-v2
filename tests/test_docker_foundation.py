from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
COMPOSE = ROOT / "infrastructure" / "compose" / "docker-compose.yml"
DOCKERFILE = ROOT / "infrastructure" / "docker" / "Dockerfile"
ENTRYPOINT = ROOT / "src" / "meylux" / "runtime" / "service.py"


class DockerFoundationTests(unittest.TestCase):
    def test_required_foundation_files_exist(self) -> None:
        for path in (COMPOSE, DOCKERFILE, ENTRYPOINT):
            self.assertTrue(path.is_file(), path)

    def test_compose_defines_governed_service_topology(self) -> None:
        text = COMPOSE.read_text(encoding="utf-8")
        for service in ("db:", "redis:", "api:", "collector:", "worker-quant:", "worker-ai:"):
            self.assertRegex(text, rf"(?m)^  {re.escape(service)}$")
        self.assertIn("name: meylux-net", text)
        self.assertIn("meylux-db-data", text)
        self.assertNotRegex(text, r"(?m)^\s+ports:\s*$")

    def test_images_are_explicitly_versioned(self) -> None:
        text = COMPOSE.read_text(encoding="utf-8")
        self.assertIn("timescale/timescaledb:2.29.2-pg16", text)
        self.assertIn("redis:7.4.6-alpine", text)
        self.assertIn("python:3.12.11-slim", DOCKERFILE.read_text(encoding="utf-8"))

    def test_no_secret_file_is_tracked_as_environment_input(self) -> None:
        dockerignore = (ROOT / ".dockerignore").read_text(encoding="utf-8")
        self.assertIn(".env", dockerignore)
        self.assertIn(".env.*", dockerignore)
        self.assertIn("!.env.example", dockerignore)


if __name__ == "__main__":
    unittest.main()
