from __future__ import annotations

import ast
import re
import sys
from pathlib import Path
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN = [
    re.compile("".join(["j", "o", "z", "e", "f"]), re.IGNORECASE),
    re.compile("".join(["o", "r", "a", "n", "g", "e", "b", "t", "c"]), re.IGNORECASE),
    re.compile("".join(["v", "c", "p", "_"]) + r"[A-Za-z0-9]+"),
    re.compile("".join(["s", "b", "p", "_"]) + r"[A-Za-z0-9]+"),
    re.compile("".join(["P", "a", "y", "m", "e", "n", "t", "s", "2", "0", "2", "5"])),
]


def iter_files() -> list[Path]:
    ignored = {".git", "__pycache__", ".pytest_cache", ".ruff_cache"}
    return [
        path
        for path in ROOT.rglob("*")
        if path.is_file() and not any(part in ignored for part in path.parts)
    ]


def main() -> int:
    failed = False

    manifest = ROOT / "makepay_odoo" / "__manifest__.py"
    if not manifest.exists():
        print("Missing Odoo manifest.", file=sys.stderr)
        failed = True

    for path in iter_files():
        text = path.read_text(encoding="utf-8")
        relative = path.relative_to(ROOT)

        for pattern in FORBIDDEN:
            if pattern.search(text):
                print(f"{relative} contains forbidden or sensitive text.", file=sys.stderr)
                failed = True

        if path.suffix == ".py":
            try:
                ast.parse(text, filename=str(path))
            except SyntaxError as exc:
                print(f"{relative}: {exc}", file=sys.stderr)
                failed = True

        if path.suffix == ".xml":
            try:
                ElementTree.fromstring(text)
            except ElementTree.ParseError as exc:
                print(f"{relative}: invalid XML: {exc}", file=sys.stderr)
                failed = True

    if failed:
        return 1

    print("Odoo module files are valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
