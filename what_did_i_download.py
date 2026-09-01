#what did i download? is a small helpful utility tool that generates a report of all the junk scattered in the downloads folder


from __future__ import annotations
import argparse
import os
import sys
import mimetypes
from pathlib import Path
from collections import defaultdict, Counter
import datetime
import html

EXT_CATEGORIES = {
    'documents': {'.pdf', '.doc', '.docx', '.odt', '.xls', '.xlsx', '.ppt', '.pptx', '.txt', '.rtf'},
    'images': {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.bmp', '.tiff', '.tif'},
    'music': {'.mp3', '.m4a', '.flac', '.wav', '.ogg', '.aac'},
    'videos': {'.mp4', '.mkv', '.mov', '.avi', '.webm', '.flv'},
    'archives': {'.zip', '.tar', '.gz', '.tgz', '.rar', '.7z', '.bz2'},
    'code': {'.py', '.js', '.ts', '.java', '.c', '.cpp', '.h', '.cs', '.go', '.rb', '.php', '.rs'},
    'presentations': {'.ppt', '.pptx'},
    'spreadsheets': {'.xls', '.xlsx', '.csv'},
}

FALLBACK_OTHER = 'others'


def human_readable_size(nbytes: int) -> str:
    if nbytes < 1024:
        return f"{nbytes} B"
    for unit in ['KB', 'MB', 'GB', 'TB', 'PB']:
        nbytes /= 1024.0
        if nbytes < 1024.0:
            return f"{nbytes:3.1f} {unit}"
    return f"{nbytes:.1f} PB"


def classify(path: Path) -> str:
    """Classify a file into our categories using extension and MIME type."""
    ext = path.suffix.lower()
    if ext:
        for cat, exts in EXT_CATEGORIES.items():
            if ext in exts:
                return cat
    # fallback to mime type
    mime, _ = mimetypes.guess_type(str(path))
    if mime:
        main = mime.split('/')[0]
        if main == 'image':
            return 'images'
        if main == 'video':
            return 'videos'
        if main == 'audio':
            return 'music'
        if main == 'text':
            return 'documents'
    return FALLBACK_OTHER


def scan_folder(folder: Path):
    stats = {
        'total_files': 0,
        'total_size': 0,
        'by_category': Counter(),
        'category_sizes': defaultdict(int),
        'largest': [],  # list of (size, path, mtime)
    }

    for root, dirs, files in os.walk(folder, followlinks=False):
        for name in files:
            try:
                p = Path(root) / name
                if not p.is_file():
                    continue
                size = p.stat().st_size
                mtime = p.stat().st_mtime
                stats['total_files'] += 1
                stats['total_size'] += size
                cat = classify(p)
                stats['by_category'][cat] += 1
                stats['category_sizes'][cat] += size
                stats['largest'].append((size, str(p), mtime))
            except PermissionError:
                # skip unreadable files
                continue
            except FileNotFoundError:
                # file vanished between os.walk and stat
                continue

    stats['largest'].sort(reverse=True, key=lambda x: x[0])
    return stats


def build_report(stats, folder: Path, top_n=10):
    now = datetime.datetime.now()
    total_files = stats['total_files']
    total_size = stats['total_size']
    category_counts = stats['by_category']
    category_sizes = stats['category_sizes']
    largest = stats['largest'][:top_n]

    
    categories = []
    for cat, count in category_counts.items():
        size = category_sizes.get(cat, 0)
        percent = (size / total_size * 100) if total_size else 0.0
        categories.append((cat, count, size, percent))
    categories.sort(key=lambda x: x[2], reverse=True)

    report = {
        'generated_at': now.isoformat(),
        'scanned_folder': str(folder),
        'total_files': total_files,
        'total_size': total_size,
        'categories': categories,
        'largest': largest,
    }
    return report


def generate_html(report, out_path: Path):
    title = 'What did I download? — Report'
    esc = html.escape
    rows = []
    for cat, count, size, pct in report['categories']:
        rows.append(f"<tr><td>{esc(cat)}</td><td>{count}</td><td>{esc(human_readable_size(size))}</td><td>{pct:.1f}%</td></tr>")

    largest_rows = []
    for size, path, mtime in report['largest']:
        mtime_s = datetime.datetime.fromtimestamp(mtime).isoformat(sep=' ', timespec='seconds')
        # create file:// link for local file
        href = 'file://' + path
        largest_rows.append(f"<tr><td><a href=\"{esc(href)}\">{esc(path)}</a></td><td>{esc(human_readable_size(size))}</td><td>{esc(mtime_s)}</td></tr>")

    total_size_hr = human_readable_size(report['total_size'])

    html_text = f"""
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{esc(title)}</title>
<style>
body {{ font-family: system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial; margin: 24px; }}
h1 {{ margin-bottom: 4px; }}
.header {{ color: #444; margin-bottom: 18px; }}
.card {{ padding: 12px; border: 1px solid #eee; border-radius: 8px; margin-bottom: 16px; box-shadow: 0 1px 2px rgba(0,0,0,0.02); }}
table {{ width: 100%; border-collapse: collapse; margin-top: 8px; }}
th, td {{ text-align: left; padding: 8px; border-bottom: 1px solid #f0f0f0; font-size: 14px; }}
th {{ background: #fafafa; font-weight: 600; color: #222; }}
.bar {{ height: 14px; background: linear-gradient(90deg,#4f46e5,#06b6d4); border-radius: 8px; }}
.small {{ color: #666; font-size: 13px }}
</style>
</head>
<body>
<h1>{esc(title)}</h1>
<div class="header small">Generated: {esc(report['generated_at'])} · Scanned folder: {esc(report['scanned_folder'])}</div>

<div class="card">
<strong>Total files:</strong> {report['total_files']}<br>
<strong>Total size:</strong> {esc(total_size_hr)}
</div>

<div class="card">
<h2>By category</h2>
<table>
<thead><tr><th>Category</th><th>Count</th><th>Size</th><th>% of space</th></tr></thead>
<tbody>
{''.join(rows)}
</tbody>
</table>
</div>

<div class="card">
<h2>Largest files (top {len(report['largest'])})</h2>
<table>
<thead><tr><th>Path</th><th>Size</th><th>Modified</th></tr></thead>
<tbody>
{''.join(largest_rows)}
</tbody>
</table>
</div>

</body>
</html>
"""

    out_path.write_text(html_text, encoding='utf-8')


def print_summary(report, top_n=10):
    print('What did I download? — Summary')
    print('Scanned folder:', report['scanned_folder'])
    print('Generated at:', report['generated_at'])
    print('Total files:', report['total_files'])
    print('Total size:', human_readable_size(report['total_size']))
    print('\nBy category:')
    for cat, count, size, pct in report['categories']:
        print(f"  {cat:12} {count:8d} files   {human_readable_size(size):>8}   {pct:5.1f}%")
    print('\nLargest files:')
    for size, path, mtime in report['largest'][:top_n]:
        print(f"  {human_readable_size(size):>8}  {path}")


def default_download_path() -> Path:
    home = Path.home()
    d1 = home / 'Downloads'
    d2 = home / 'downloads'
    if d1.exists():
        return d1
    if d2.exists():
        return d2
    return d1


def main(argv=None):
    parser = argparse.ArgumentParser(description='Scan downloads folder and generate a dashboard report')
    parser.add_argument('--path', '-p', help='Folder to scan (default: ~/Downloads)', default=None)
    parser.add_argument('--top', '-t', help='Number of largest files to include', type=int, default=10)
    parser.add_argument('--output', '-o', help='Output HTML file', default='report.html')
    args = parser.parse_args(argv)

    folder = Path(args.path) if args.path else default_download_path()
    folder = folder.expanduser().resolve()
    if not folder.exists() or not folder.is_dir():
        print(f"Error: folder does not exist: {folder}", file=sys.stderr)
        sys.exit(2)

    stats = scan_folder(folder)
    report = build_report(stats, folder, top_n=args.top)
    out_path = Path(args.output)
    generate_html(report, out_path)
    print_summary(report, top_n=args.top)
    print('\nReport written to:', out_path)


if __name__ == '__main__':
    main()
