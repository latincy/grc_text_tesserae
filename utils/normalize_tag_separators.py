"""Normalize the whitespace separating a Tesserae citation tag from its text.

The corpus mixes three separator styles: a single space (the majority form),
a bare tab, and a tab followed by further spaces. This rewrites every
separator to a single space, leaving tag internals and line text untouched.
A tag with nothing after it keeps no trailing separator.

Usage: normalize_tag_separators.py <texts-dir> [--dry-run]
"""

import re
import sys
from pathlib import Path

SEP_RE = re.compile(r"^(<[^>]+>)[ \t]+(.*)$")


def normalize(text: str) -> tuple[str, int]:
    out, changed = [], 0
    for line in text.split("\n"):
        m = SEP_RE.match(line)
        if m:
            tag, rest = m.group(1), m.group(2)
            new = f"{tag} {rest}" if rest.strip() else tag
            if new != line:
                changed += 1
            out.append(new)
        else:
            out.append(line)
    return "\n".join(out), changed


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    dry_run = "--dry-run" in sys.argv
    if not args:
        print(__doc__)
        return 2

    texts = Path(args[0]).resolve()
    files = sorted(texts.glob("*.tess"))
    if not files:
        print(f"No .tess files in {texts}")
        return 1

    touched = total = 0
    for path in files:
        original = path.read_text(encoding="utf-8")
        updated, changed = normalize(original)
        if changed:
            touched += 1
            total += changed
            if not dry_run:
                path.write_text(updated, encoding="utf-8")

    verb = "would change" if dry_run else "changed"
    print(f"{verb} {total} lines across {touched} of {len(files)} files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
