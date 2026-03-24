from __future__ import annotations

import unittest

from book_crawler.brave_search import parse_brave_search_output


class BraveSearchParsingTests(unittest.TestCase):
    def test_parse_brave_search_output(self) -> None:
        output = """--- Result 1 ---
Title: Think Python How to Think Like a Computer Scientist Version 2.0.17
Link: https://www.greenteapress.com/thinkpython/thinkpython.pdf
Snippet: The result is this book, now with the less grandiose title Think Python. Allen B. Downey

--- Result 2 ---
Title: Allen B. Downey Think Python HOW TO THINK LIKE A COMPUTER SCIENTIST 2nd Edition
Link: http://facweb.cs.depaul.edu/sjost/it211/documents/think-python-2nd.pdf
Snippet: Allen B. Downey Think Python HOW TO THINK LIKE A COMPUTER SCIENTIST
"""
        results = parse_brave_search_output(output)

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].title, "Think Python How to Think Like a Computer Scientist Version 2.0.17")
        self.assertEqual(results[0].link, "https://www.greenteapress.com/thinkpython/thinkpython.pdf")
        self.assertIn("Allen B. Downey", results[0].snippet)


if __name__ == "__main__":
    unittest.main()
