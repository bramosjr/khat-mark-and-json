import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from build_version_info import generate_version_info, write_version_info, read_app_version


class TestBuildVersionInfo(unittest.TestCase):
    def test_generate_version_info_has_expected_fields(self):
        info = generate_version_info("0.1.7", "1.0.0", built_at="2026-09-08T00:00:00+00:00")
        self.assertEqual(info, {
            "app_version": "1.0.0",
            "markitdown_version": "0.1.7",
            "built_at": "2026-09-08T00:00:00+00:00",
        })

    def test_write_version_info_writes_valid_json(self):
        info = generate_version_info("0.1.7", "1.0.0", built_at="2026-09-08T00:00:00+00:00")
        with TemporaryDirectory() as tmp:
            output_path = Path(tmp) / "dist" / "version-info.json"
            write_version_info(info, output_path)
            with open(output_path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            self.assertEqual(loaded, info)

    def test_read_app_version_reads_version_field(self):
        with TemporaryDirectory() as tmp:
            package_json = Path(tmp) / "package.json"
            package_json.write_text(json.dumps({"version": "1.0.0", "name": "frontend"}), encoding="utf-8")
            self.assertEqual(read_app_version(package_json), "1.0.0")


if __name__ == "__main__":
    unittest.main()
