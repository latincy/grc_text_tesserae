"""Normalize Greek surface encoding across the corpus: unify elision marks to
U+2019 and the ano teleia to U+00B7. Operates on .tess body text only; citation
tags are left untouched (verified to contain no ':' or apostrophe characters).

Rationale and conventions
-------------------------
Elision -> U+2019 (RIGHT SINGLE QUOTATION MARK):
    This corpus spells the elision mark five different ways --
        U+0027  ASCII apostrophe            (240k)
        U+1FBD  Greek koronis, used here as elision, not crasis
                (5,313 / 5,335 are word-final: ἀπ᾽, ἀλλ᾽, καθ᾽, ἐπ᾽ ...)
        U+02BC  modifier letter apostrophe
        U+1FBF  Greek psili (spiritus lenis) standing in for the mark
        U+0313  dangling combining smooth breathing on a consonant
    All are unified to U+2019, the canonical elision codepoint used by the
    LatinCy grc pipeline's normalize_surface() and the prevailing target in
    digital-Greek normalization (cf. J. Tauber, greek-normalisation; MorphGNT /
    First1KGreek practice). U+2019 is also the Unicode-preferred punctuation
    apostrophe (Unicode Standard, "Apostrophes").
    Genuine CRASIS (κἀγώ, τἀληθῆ) is a composed vowel + smooth breathing after
    NFC, never a standalone mark, so it is NOT affected -- only the standalone
    elision marks above are.

Ano teleia -> U+00B7 (MIDDLE DOT):
    ASCII ':' is used in this corpus for the Greek raised-dot punctuation. The
    Unicode-canonical raised dot is U+00B7: U+0387 GREEK ANO TELEIA has a
    canonical decomposition to U+00B7, so U+00B7 is the NFC-stable form (this is
    also what normalize_surface() assumes). Colons immediately adjacent to a
    digit (11 of them) are stray-OCR-digit artifacts or an embedded cross-
    reference (`ιλ. 14.296:`); they are left as-is for the separate digit pass.

Deliberately NOT changed: genuine crasis; macrons/breves (U+0304/U+0306, which
are meaningful vowel-length marks the source editions carry -- the pipeline
strips them at tokenization time, not in the source corpus); quotation marks.

Output is NFC. Run with --apply to write; default is a dry run.
"""

import glob
import sys
import unicodedata
from collections import Counter
from pathlib import Path

APPLY = "--apply" in sys.argv
TEXTS = Path(__file__).parent.parent / "texts"

ELISION_MARKS = ["'", "᾽", "ʼ", "᾿"]  # -> U+2019
RSQUO = "’"
ANO_TELEIA = "·"


def normalize_body(body: str, tally: Counter) -> str:
    body = unicodedata.normalize("NFC", body)
    # dangling combining smooth breathing (elision on a consonant) -> U+2019
    if "̓" in body:
        tally["U+0313"] += body.count("̓")
        body = body.replace("̓", RSQUO)
    for mark in ELISION_MARKS:
        if mark in body:
            tally[f"U+{ord(mark):04X}"] += body.count(mark)
            body = body.replace(mark, RSQUO)
    # ano teleia: ASCII ':' -> U+00B7, except digit-adjacent (left for digit pass)
    if ":" in body:
        out = []
        for i, ch in enumerate(body):
            if ch == ":":
                prev = body[i - 1] if i > 0 else ""
                nxt = body[i + 1] if i + 1 < len(body) else ""
                if prev.isdigit() or nxt.isdigit():
                    out.append(ch)
                    tally["colon_kept"] += 1
                else:
                    out.append(ANO_TELEIA)
                    tally["U+003A"] += 1
            else:
                out.append(ch)
        body = "".join(out)
    return unicodedata.normalize("NFC", body)


def main() -> int:
    tally = Counter()
    files_changed = 0
    for fp in sorted(TEXTS.glob("*.tess")):
        lines = fp.read_text(encoding="utf-8").split("\n")
        changed = False
        for i, line in enumerate(lines):
            if not line:
                continue
            # split tag from the rest at the first '>' (tags carry no ':'/apostrophe)
            if line.startswith("<") and ">" in line:
                cut = line.index(">") + 1
                tag, rest = line[:cut], line[cut:]
                new_rest = normalize_body(rest, tally)
                if new_rest != rest:
                    lines[i] = tag + new_rest
                    changed = True
            else:
                new_line = normalize_body(line, tally)
                if new_line != line:
                    lines[i] = new_line
                    changed = True
        if changed:
            files_changed += 1
            if APPLY:
                fp.write_text("\n".join(lines), encoding="utf-8")

    print(("APPLIED" if APPLY else "DRY RUN") + f" — files changed: {files_changed}")
    print(f"  elision -> U+2019:")
    for k in ("U+0027", "U+1FBD", "U+02BC", "U+1FBF", "U+0313"):
        if tally[k]:
            print(f"      {tally[k]:>7}  {k}")
    print(f"  ano teleia ':' -> U+00B7: {tally['U+003A']}   (digit-adjacent kept: {tally['colon_kept']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
