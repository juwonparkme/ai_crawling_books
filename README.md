# ai_crawling_books


Design notes and flow:
- `book_crawler/flow.md`
- `book_crawler/licensing.md`

Install:
```bash
python3 -m pip install -r requirements.txt
```

Run:
```bash
mkdir -p /tmp/books
python3 -m book_crawler --title "Database System Concepts" --author "Silberschatz" --out /tmp/books --dry-run
```
