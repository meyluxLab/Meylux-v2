import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]


class RepositoryFoundationTests(unittest.TestCase):
    def test_python_metadata_exists(self):
        metadata = ROOT / "pyproject.toml"
        self.assertTrue(metadata.is_file())
        text = metadata.read_text(encoding="utf-8")
        self.assertIn('requires-python = ">=3.12,<3.14"', text)
        self.assertIn('version = "2.0.0"', text)

    def test_package_foundation_exists(self):
        package = ROOT / "src" / "meylux" / "__init__.py"
        self.assertTrue(package.is_file())

    def test_required_top_level_foundation_dirs_exist(self):
        for path in (
            "config",
            "contracts",
            "infrastructure",
            "migrations",
            "src",
            "tests",
        ):
            self.assertTrue((ROOT / path).is_dir(), path)


if __name__ == "__main__":
    unittest.main()
