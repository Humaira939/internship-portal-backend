"""Finds the frontend pages (plain Python: only pathlib, so it is easy to test).
 
Every file  html/<name>.html  becomes the route  /<name>   (index.html becomes  /).
A new page added by the frontend member gets its route automatically, nothing to register.
"""
import re
from pathlib import Path
 
PAGE_FILE = re.compile(r"^[A-Za-z0-9_-]+\.html$")
TEMPLATE_SYNTAX = ("{{", "{%", "{#")      # Jinja2 would treat these as template code
 
 
def discover_pages(html_dir: Path) -> dict:
    """{'/': 'index.html', '/login': 'login.html', ...}"""
    pages = {}
    if not html_dir.is_dir():
        return pages
 
    for file in sorted(html_dir.iterdir()):
        if not file.is_file() or not PAGE_FILE.match(file.name):
            continue
        route = "/" if file.stem == "index" else f"/{file.stem}"
        pages[route] = file.name
    return pages
 
 
def template_conflicts(html_dir: Path, pages: dict) -> list:
    """Page files that contain {{ {% or {#  (they would be read as template code). Normally an empty list."""
    problems = []
    for filename in pages.values():
        try:
            text = (html_dir / filename).read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if any(marker in text for marker in TEMPLATE_SYNTAX):
            problems.append(filename)
    return problems
 