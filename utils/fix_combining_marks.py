"""Repair mis-ordered Greek diacritics in the corpus body text.

Two related corruptions, both a diacritic printed BEFORE its base letter so NFC
cannot compose it:

1. Mis-ordered COMBINING marks (U+0300-U+036F: accents, rough breathing U+0314,
   iota subscript, diaeresis) before their base letter — e.g. `̔Ρ` for Ῥ,
   `́Η` for Ή, `“̔́Ο` for `“Ὅ`.

2. Mis-ordered SMOOTH breathings that the v0.6 elision pass turned into stray
   apostrophes. v0.6 mapped dangling U+0313 (and U+1FBF/U+1FBD) to U+2019,
   assuming any leftover was an elision mark on a consonant; but where the smooth
   breathing was mis-ordered BEFORE a vowel it did not compose, so it became a
   spurious `’` (e.g. `“’Ατυχὴ` for `“Ἀτυχὴ`, `“’́Ηδη` for `“Ἤδη`). This is fully
   recoverable: rough breathings stayed combining (`̔`) while smooth became `’`,
   and a word-initial `’`+vowel is ALWAYS a smooth breathing (vowel-initial Greek
   words always carry one; elisions never begin a word).

Fix: a word-initial diacritic cluster (a run of `’` and/or combining marks NOT
preceded by a Greek letter) that is followed by a base letter is reordered onto
that letter and NFC-composed; a `’` in the cluster is restored as U+0313 smooth
breathing (only onto a vowel). Handles a non-letter prefix such as a quotation
mark, and multi-mark clusters (`“’́Η` -> `“Ἤ`).

Left untouched: diacritics already correctly following a letter; genuine
elisions (`’` preceded by a letter / followed by a space). HELD and logged:
clusters with no adjacent base letter (floating, e.g. `ς ̔ ἐπ`) and a `’` smooth
breathing that would fall on a non-vowel — these need source judgment.

Body text only; NFC-safe. Run with --apply to write; default is a dry run.
A markdown review artifact is written to REVIEW_PATH.
"""

import sys
import unicodedata
from collections import Counter
from pathlib import Path

APPLY = "--apply" in sys.argv
TEXTS = Path(__file__).parent.parent / "texts"
REVIEW_PATH = Path(__file__).parent.parent / "REPAIR_REVIEW_COMBINING.md"
SMOOTH = "̓"
VOWELS = set("αεηιουωΑΕΗΙΟΥΩ")


def is_combining(c: str) -> bool:
    return unicodedata.combining(c) != 0


def is_greek_letter(c: str) -> bool:
    return c.isalpha() and (0x370 <= ord(c) <= 0x3FF or 0x1F00 <= ord(c) <= 0x1FFF)


def ctx(s: str, a: int, b: int, w: int = 14) -> str:
    return s[max(0, a - w):a] + "⟦" + s[a:b] + "⟧" + s[b:b + w]


def process_body(body: str, applied: list, held: list, tally: Counter) -> str:
    body = unicodedata.normalize("NFC", body)
    out = []
    i, n = 0, len(body)
    while i < n:
        c = body[i]
        starts = c == "’" or is_combining(c)
        prev_letter = i > 0 and is_greek_letter(body[i - 1])
        if not (starts and not prev_letter):
            out.append(c)
            i += 1
            continue
        # consume a cluster of ’ and combining marks
        j = i
        has_smooth = False
        marks = []
        while j < n and (body[j] == "’" or is_combining(body[j])):
            if body[j] == "’":
                has_smooth = True
            else:
                marks.append(body[j])
            j += 1
        base = body[j] if j < n else ""
        comb = "".join(marks)
        if not (base and is_greek_letter(base)):
            # no base letter to attach to -> floating (also covers a lone word-initial ’)
            held.append((ctx(body, i, j), "floating / no base"))
            tally["held (floating)"] += 1
            out.append(body[i:j])
            i = j
            continue
        if has_smooth and base not in VOWELS:
            held.append((ctx(body, i, j + 1), "smooth breathing on non-vowel"))
            tally["held (non-vowel)"] += 1
            out.append(body[i:j])
            i = j
            continue
        breathing = SMOOTH if has_smooth else ""
        fixed = unicodedata.normalize("NFC", base + breathing + comb)
        applied.append((ctx(body, i, j + 1), "smooth" if has_smooth else "combining"))
        tally["breathing restored" if has_smooth else "combining reordered"] += 1
        tally["composed"] += 1 if len(fixed) == 1 else 0
        out.append(fixed)
        i = j + 1
    return unicodedata.normalize("NFC", "".join(out))


def main() -> int:
    applied, held, tally = [], [], Counter()
    files_changed = 0
    for fp in sorted(TEXTS.glob("*.tess")):
        lines = fp.read_text(encoding="utf-8").split("\n")
        changed = False
        for i, line in enumerate(lines):
            if not line:
                continue
            if line.startswith("<") and ">" in line:
                cut = line.index(">") + 1
                new = line[:cut] + process_body(line[cut:], applied, held, tally)
            else:
                new = process_body(line, applied, held, tally)
            if new != line:
                lines[i] = new
                changed = True
        if changed:
            files_changed += 1
            if APPLY:
                fp.write_text("\n".join(lines), encoding="utf-8")

    smooth = [s for s, k in applied if k == "smooth"]
    comb = [s for s, k in applied if k == "combining"]
    md = ["# Diacritic reorder / breathing restore — review\n",
          f"Mode: {'APPLIED' if APPLY else 'DRY RUN'} · files changed: {files_changed}\n",
          f"## Smooth breathing restored (’ -> U+0313 on vowel) — {len(smooth)}\n"]
    for s in smooth[:150]:
        md.append(f"- `{s}`")
    if len(smooth) > 150:
        md.append(f"- …+{len(smooth) - 150} more")
    md.append(f"\n## Combining mark reordered — {len(comb)}\n")
    for s in comb[:150]:
        md.append(f"- `{s}`")
    if len(comb) > 150:
        md.append(f"- …+{len(comb) - 150} more")
    md.append(f"\n## HELD — {len(held)}\n")
    for s, reason in held[:150]:
        md.append(f"- [{reason}] `{s}`")
    if len(held) > 150:
        md.append(f"- …+{len(held) - 150} more")
    REVIEW_PATH.write_text("\n".join(md), encoding="utf-8")

    print(("APPLIED" if APPLY else "DRY RUN") + f" — files changed: {files_changed}")
    print(f"  smooth breathing restored (’->breathing): {tally['breathing restored']}")
    print(f"  combining mark reordered:                 {tally['combining reordered']}")
    print(f"  composed to a single codepoint:           {tally['composed']}")
    print(f"  held (floating / non-vowel):              {tally['held (floating)'] + tally['held (non-vowel)']}")
    print(f"  review artifact: {REVIEW_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
