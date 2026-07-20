"""Remove non-original Arabic-digit artifacts from the corpus body text.

Ancient Greek used alphabetic numerals, not Arabic digits, so every Arabic digit
in the body is a modern intrusion: a leaked edition/section marker, a
transliterated source-reference, or an OCR artifact. This pass removes the
*mechanical, source-independent* classes and HOLDS the source-dependent ones
(transliterated references, letter-substitution OCR) for review against the
original editions.

Order matters: systematic markers are stripped first (many `Σ\\d+` sigla sit
between Greek letters and would otherwise look like in-word strays); only the
residual in-word digits are the clean `σ2`-type insertions.

APPLIED (mechanical):
  Tier 1 - systematic markers, deleted (word halves rejoin):
      Σ\\d+            scholium siglum  (μ’Σ32, ὦγ -> μ’, ὦγ)
      ["“]\\d+         line/quote markers  (Καρ"1χηδονίοις -> Καρχηδονίοις)
      %\\d+            paragraph markers  (%5εἰπὼν -> εἰπὼν)
      #\\d+            apparatus markers
      \\[\\d+          apparatus markers  ([1καὶ -> καὶ)
  Tier 3 - in-word stray digit with a Greek letter on BOTH sides, deleted and
      rejoined, IFF the rejoined token is a plausible Greek word length (<= MAXLEN).
      The dominant case is σ+digit insertion (ὥσ2περ -> ὥσπερ, τοιόσ2δε -> τοιόσδε).
  Colon cleanup - after digit removal, any ASCII ':' no longer adjacent to a digit
      is converted to U+00B7 ano teleia (finishing the v0.6 encoding pass, which
      deliberately left 11 digit-adjacent colons for this pass).

HELD (needs the source edition; written to the review artifact, NOT changed):
  - Transliterated source-references (ηομ. ιλ. X.Y, ναυξκ N, ηες. ωδ N, ...):
    standalone / decimal / range / hyphen digits, and digits attached to
    unaccented transliterated tokens.
  - Letter-substitution OCR and word-boundary splits (λαβάργυροσ2ὡρολογητής,
    where the digit marks a missing space, not a rejoin).

Body text only; citation tags carry no digits of these classes. NFC-safe.
Run with --apply to write; default is a dry run. A markdown review artifact of
every proposed and held change is written to REVIEW_PATH.
"""

import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path

APPLY = "--apply" in sys.argv
TEXTS = Path(__file__).parent.parent / "texts"
REVIEW_PATH = Path(__file__).parent.parent / "REPAIR_REVIEW_DIGITS.md"
MAXLEN = 18  # max plausible Greek token length for an auto in-word rejoin

# Tier 1 systematic markers: (name, compiled pattern). Deleted entirely.
# NOTE: `#\d+` is deliberately NOT here — it is entangled with geometric
# point-labels (Ω#4), citation refs (Πολύβιος ι#2#), and chapter headings
# (Ι#2 Ὅπως ...); it is left for the source-review batch.
MARKERS = [
    ("Σ\\d+ siglum", re.compile(r"Σ\d+")),
    ('["“]\\d+ line/quote', re.compile(r'["“]\d+')),
    ("%\\d+", re.compile(r"%\d+")),
    ("\\[\\d+", re.compile(r"\[\d+")),
]

WORDCH = re.compile(r"[Ͱ-Ͽἀ-῿̀-ͯ’]")
VOWELS = set("αειουηωΑΕΙΟΥΗΩάέίόύήώὰὲὶὸὺὴὼᾶῆῶἀἁἐἑἠἡἰἱὀὁὐὑὠὡ")


def is_greek(ch: str) -> bool:
    return bool(ch) and bool(WORDCH.match(ch)) and ch != "’"


def token_around(s: str, i: int) -> str:
    """Maximal word token spanning index i (a digit), with the digit removed."""
    a = i
    while a > 0 and WORDCH.match(s[a - 1]):
        a -= 1
    b = i + 1
    while b < len(s) and WORDCH.match(s[b]):
        b += 1
    return s[a:i] + s[i + 1:b]


def ctx(s: str, i: int, j: int, w: int = 18) -> str:
    return s[max(0, i - w):i] + "⟦" + s[i:j] + "⟧" + s[j:j + w]


def process_body(body: str, applied: dict, held: list, tally: Counter):
    body = unicodedata.normalize("NFC", body)

    # Tier 1: strip systematic markers (record context before removing).
    def record(name, m):
        applied.setdefault(name, []).append(ctx(body, m.start(), m.end()))
        tally[name] += 1

    # "N / “N line-quote markers -> delete (Polybius line-splits merge correctly)
    name = '["“]\\d+ line/quote'
    for m in re.finditer(r'["“]\d+', body):
        record(name, m)
    body = re.sub(r'["“]\d+', "", body)

    # ΣN scholium siglum -> delete
    name = "Σ\\d+ siglum"
    for m in re.finditer(r"Σ\d+", body):
        record(name, m)
    body = re.sub(r"Σ\d+", "", body)

    # %N paragraph marker -> a space when it sits between two Greek letters
    # (word boundary, e.g. γάρ%5περὶ -> γάρ περὶ), else delete
    name = "%\\d+"
    for m in re.finditer(r"%\d+", body):
        record(name, m)

    def _pct(m):
        pb = body[m.start() - 1] if m.start() > 0 else ""
        na = body[m.end()] if m.end() < len(body) else ""
        return " " if is_greek(pb) and is_greek(na) else ""

    body = re.sub(r"%\d+", _pct, body)

    # [N apparatus marker, only when a Greek letter follows ([1καὶ); a bare
    # "[3, 1 — 6, 4" reference falls through to the HELD classifier below
    name = "\\[\\d+"
    br = re.compile(r"\[\d+(?=[Ͱ-Ͽἀ-῿])")
    for m in br.finditer(body):
        record(name, m)
    body = br.sub("", body)

    # collapse double spaces created by marker removal (regular spaces only)
    body = re.sub(r"  +", " ", body)

    # Tier 3 + HELD: classify each remaining digit run
    out = []
    k = 0
    for m in re.finditer(r"\d+", body):
        out.append(body[k:m.start()])
        i, j = m.start(), m.end()
        run = m.group(0)
        pb = body[i - 1] if i > 0 else ""
        na = body[j] if j < len(body) else ""
        approve = False
        if len(run) == 1 and run != "0" and is_greek(pb) and is_greek(na):
            # token boundaries with the digit removed
            a = i
            while a > 0 and WORDCH.match(body[a - 1]):
                a -= 1
            b = j
            while b < len(body) and WORDCH.match(body[b]):
                b += 1
            left, right = body[a:i], body[i + 1:b]
            tok = left + right
            clean = all(WORDCH.match(c) for c in tok)  # no ? / Latin / stray digit
            before = body[a - 1] if a > 0 else " "
            lone_consonant = len(left) == 1 and left not in VOWELS and before == " "
            if clean and len(tok) <= MAXLEN and not lone_consonant:
                approve = True
        if approve:
            applied.setdefault("in-word stray", []).append(ctx(body, i, j))
            tally["in-word stray"] += 1
            k = j
            continue  # drop the digit
        # reason for holding
        if len(run) == 1 and is_greek(pb) and is_greek(na):
            reason = "in-word, held (garbage/0/boundary — needs source)"
        elif is_greek(pb) or is_greek(na):
            reason = "digit attached to word edge"
        elif re.match(r"\d", pb) or na == "." or pb in ".-":
            reason = "decimal/range reference"
        else:
            reason = "standalone number / reference"
        held.append((reason, ctx(body, i, j)))
        tally["HELD:" + reason] += 1
        out.append(run)  # keep held digit
        k = j
    out.append(body[k:])
    body = "".join(out)

    # Colon cleanup: ASCII ':' now free of an adjacent digit -> U+00B7
    res = []
    for idx, ch in enumerate(body):
        if ch == ":":
            p = body[idx - 1] if idx > 0 else ""
            n = body[idx + 1] if idx + 1 < len(body) else ""
            if not p.isdigit() and not n.isdigit():
                res.append("·")
                tally["colon->U+00B7"] += 1
                continue
        res.append(ch)
    body = "".join(res)
    return unicodedata.normalize("NFC", body)


def main() -> int:
    applied, held, tally = {}, [], Counter()
    files_changed = 0
    for fp in sorted(TEXTS.glob("*.tess")):
        lines = fp.read_text(encoding="utf-8").split("\n")
        changed = False
        for i, line in enumerate(lines):
            if not line:
                continue
            if line.startswith("<") and ">" in line:
                cut = line.index(">") + 1
                tag, rest = line[:cut], line[cut:]
                new = tag + process_body(rest, applied, held, tally)
            else:
                new = process_body(line, applied, held, tally)
            if new != line:
                lines[i] = new
                changed = True
        if changed:
            files_changed += 1
            if APPLY:
                fp.write_text("\n".join(lines), encoding="utf-8")

    # review artifact
    md = ["# Digit-artifact pass — review\n",
          f"Mode: {'APPLIED' if APPLY else 'DRY RUN'} · files changed: {files_changed}\n"]
    md.append("## Applied\n")
    for name in [n for n, _ in MARKERS] + ["in-word stray"]:
        items = applied.get(name, [])
        md.append(f"### {name} — {len(items)}")
        for s in items[:60]:
            md.append(f"- `{s}`")
        if len(items) > 60:
            md.append(f"- …+{len(items) - 60} more")
        md.append("")
    md.append(f"### colon -> U+00B7 — {tally['colon->U+00B7']}\n")
    md.append("## HELD (needs source review)\n")
    byreason = {}
    for reason, c in held:
        byreason.setdefault(reason, []).append(c)
    for reason, items in sorted(byreason.items(), key=lambda kv: -len(kv[1])):
        md.append(f"### {reason} — {len(items)}")
        for s in items[:80]:
            md.append(f"- `{s}`")
        if len(items) > 80:
            md.append(f"- …+{len(items) - 80} more")
        md.append("")
    REVIEW_PATH.write_text("\n".join(md), encoding="utf-8")

    print(("APPLIED" if APPLY else "DRY RUN") + f" — files changed: {files_changed}")
    print("  applied:")
    for name, _ in MARKERS:
        print(f"      {tally[name]:>5}  {name}")
    print(f"      {tally['in-word stray']:>5}  in-word stray (strip+rejoin)")
    print(f"      {tally['colon->U+00B7']:>5}  colon -> U+00B7")
    print("  HELD:")
    for k in sorted(tally):
        if k.startswith("HELD:"):
            print(f"      {tally[k]:>5}  {k[5:]}")
    print(f"  review artifact: {REVIEW_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
