from __future__ import annotations

import unittest

from book_crawler.license_detector import decision_for_direct_pdf


class LicenseDetectorTests(unittest.TestCase):
    def test_official_direct_pdf_is_allowed(self) -> None:
        decision = decision_for_direct_pdf(
            "Think Python Allen B. Downey official PDF",
            "www.greenteapress.com",
            120,
        )

        self.assertEqual(decision["status"], "allowed")
        self.assertEqual(decision["reason"], "official_distribution")


if __name__ == "__main__":
    unittest.main()
