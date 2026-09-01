#!/usr/bin/env python3
"""
Regenerates firmware/include/web_page.h from web/public/index.html.

web/public/index.html is the single source of truth for the control page.
Run this script every time you edit that file, then re-flash the firmware.

Usage:
    python3 scripts/generate_web_header.py
"""

import os

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE_HTML = os.path.join(REPO_ROOT, "web", "public", "index.html")
OUTPUT_HEADER = os.path.join(REPO_ROOT, "firmware", "include", "web_page.h")


def main():
    with open(SOURCE_HTML, "r", encoding="utf-8") as f:
        html = f.read()

    if ")rawliteral\"" in html or 'R"rawliteral(' in html:
        raise ValueError(
            "index.html contains the raw-literal delimiter used by this script. "
            "Rename the delimiter in this script to something not present in the HTML."
        )

    os.makedirs(os.path.dirname(OUTPUT_HEADER), exist_ok=True)

    with open(OUTPUT_HEADER, "w", encoding="utf-8") as f:
        f.write("// AUTO-GENERATED — do not edit directly.\n")
        f.write("// Source of truth: web/public/index.html\n")
        f.write("// Regenerate with: python3 scripts/generate_web_header.py\n\n")
        f.write("#pragma once\n\n")
        f.write('const char index_html[] PROGMEM = R"rawliteral(\n')
        f.write(html)
        f.write('\n)rawliteral";\n')

    print(f"Wrote {OUTPUT_HEADER} ({len(html)} bytes of HTML)")


if __name__ == "__main__":
    main()
