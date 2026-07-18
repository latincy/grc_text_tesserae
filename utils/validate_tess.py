"""Validate Tesserae citation format across all .tess files.

Every non-empty line must begin with a citation tag of the form:
    <author. work. ref>
i.e. `^<[^>]+>` followed by a tab or space then text.

Exit 0 if all files pass, 1 if any violations found.
"""

import re
import sys
from pathlib import Path

# Valid: <citation>\ttext  or  <citation> text  or  <citation>  (lacuna/empty line)
CITATION_RE = re.compile(r"^<[^>]+>([\t ].*)?$")
TEXTS_DIR = Path(__file__).parent.parent / "texts"


def validate_file(path: Path) -> list[tuple[int, str]]:
    violations = []
    with path.open(encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, 1):
            line = line.rstrip("\n")
            if not line:
                continue
            if not CITATION_RE.match(line):
                violations.append((lineno, line))
    return violations


def main() -> int:
    tess_files = sorted(TEXTS_DIR.glob("*.tess"))
    if not tess_files:
        print(f"ERROR: no .tess files found under {TEXTS_DIR}", file=sys.stderr)
        return 1

    total_violations = 0
    for path in tess_files:
        violations = validate_file(path)
        if violations:
            for lineno, line in violations:
                preview = line[:120] + ("…" if len(line) > 120 else "")
                print(f"{path.relative_to(TEXTS_DIR.parent)}:{lineno}: {preview}")
            total_violations += len(violations)

    if total_violations:
        print(
            f"\n{total_violations} citation format violation(s) across "
            f"{sum(1 for p in tess_files if validate_file(p))} file(s).",
            file=sys.stderr,
        )
        return 1

    print(f"OK — {len(tess_files)} files validated.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
