What did I download?
=====================

A small Python utility that scans a downloads folder and creates a simple HTML dashboard showing:

- Counts of files in categories (documents, images, music, videos, archives, code, others)
- Total number of files and total size
- Breakdown of size per category
- Top N largest files with links

Requirements
------------
- Python 3.7+ (uses only the standard library)

Usage
-----

From the project folder run either of these:

python3 downloadscan.py
python3 what_did_i_download.py

Options:
  --path / -p     Path to scan (default: ~/Downloads or ~/downloads)
  --top / -t      Number of largest files to include in report (default: 10)
  --output / -o   Output HTML file (default: ./report.html)

Example:

python3 what_did_i_download.py --path ~/Downloads --top 20 --output ~/downloads-report.html

Notes
-----
- The generated HTML uses file:// links for local files so it can be opened in a browser and clicked to open files in the OS.
- No external packages required.
- If the default downloads folder doesn't exist, pass --path explicitly.
