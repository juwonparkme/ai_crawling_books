from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from book_crawler.service import RunSettings, build_config, load_run_file, validate_settings


class ServiceTests(unittest.TestCase):
    def test_build_config_includes_gui_provider_setting(self) -> None:
        settings = RunSettings(
            title="Think Python",
            author="Downey",
            out_dir="result",
            search_provider="bing",
            dry_run=True,
        )

        config = build_config(settings)

        self.assertEqual(config.title, "Think Python")
        self.assertEqual(config.author, "Downey")
        self.assertEqual(config.search_provider, "bing")
        self.assertTrue(config.dry_run)

    def test_validate_settings_allows_missing_output_directory_with_existing_parent(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            settings = RunSettings(title="Think Python", out_dir=str(Path(tmpdir) / "new-result"))

            self.assertEqual(validate_settings(settings), [])

    def test_validate_settings_rejects_unknown_provider(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            settings = RunSettings(
                title="Think Python",
                out_dir=tmpdir,
                search_provider="unknown",
            )

            self.assertIn("--search-provider must be brave or bing", validate_settings(settings))

    def test_load_run_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "run_example.json"
            path.write_text('{"stats": {"total_results": 1}}', encoding="utf-8")

            payload = load_run_file(path)

        self.assertEqual(payload["stats"]["total_results"], 1)


if __name__ == "__main__":
    unittest.main()
