"""Render podcast episode summaries (markdown) to static HTML pages.

Usage: python build_summaries.py <transcripts_dir> s1e1 s1e2 ...

Reads <transcripts_dir>/<episode>/summaries/<SUMMARY_FILE>, drops the Tags
section, and writes summaries/<episode>.html.
"""
import html
import re
import sys
from pathlib import Path

SUMMARY_FILE = "claude_cli_haiku_final_summary.md"
OUT_DIR = Path(__file__).parent / "summaries"

PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="robots" content="noindex, nofollow">
<title>{title}</title>
<link rel="stylesheet" href="summary.css">
</head>
<body>
<main>
<p class="back"><a href="../">[ fatherhood + together ]</a></p>
{body}
</main>
</body>
</html>
"""


def inline(text):
    text = html.escape(text.replace(" * * *", ""), quote=False)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    return re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)


def drop_tags_section(lines):
    out, skipping = [], False
    for line in lines:
        if line.strip() == "**Tags**":
            skipping = True
        elif skipping and line.strip() == "---":
            skipping = False
        if not skipping:
            out.append(line)
    return out


def render(markdown):
    parts, para, items = [], [], []

    def flush():
        nonlocal para, items
        if items:
            parts.append("<ul>" + "".join(f"<li>{i}</li>" for i in items) + "</ul>")
            items = []
        if para:
            parts.append("<p>" + inline("\n".join(para)) + "</p>")
            para = []

    for raw in drop_tags_section(markdown.splitlines()):
        line = raw.strip()
        heading = re.match(r"(#{1,3}) (.+)", line)
        if not line:
            flush()
        elif heading:
            flush()
            level = len(heading.group(1))
            parts.append(f"<h{level}>{inline(heading.group(2))}</h{level}>")
        elif line == "---":
            flush()
            parts.append("<hr>")
        elif line.startswith("- "):
            if para:
                flush()
            items.append(inline(line[2:]))
        else:
            if items:
                flush()
            para.append(line)
    flush()
    return "\n".join(parts)


def main(transcripts_dir, episodes):
    OUT_DIR.mkdir(exist_ok=True)
    for ep in episodes:
        source = Path(transcripts_dir) / ep / "summaries" / SUMMARY_FILE
        markdown = source.read_text(encoding="utf-8")
        title = html.escape(re.match(r"# (.+)", markdown).group(1), quote=False)
        out = OUT_DIR / f"{ep}.html"
        out.write_text(PAGE.format(title=title, body=render(markdown)), encoding="utf-8")
        print(f"wrote {out}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2:])
