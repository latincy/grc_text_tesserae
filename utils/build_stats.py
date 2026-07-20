"""Generate the collection `stats/` folder: a corpus-level summary plus one
per-.tess summary file, in the spirit of an NLTK CorpusReader `corpus_info`
(cf. https://bbengfort.github.io/2016/04/nltk-corpus-reader/).

The Tesserae unit of structure is the CITATION LINE (`<author. work. ref>\\ttext`)
— a verse line for poetry, a section for prose — so it stands in for the
paragraph/sentence counts of a plain-text corpus.

Writes:
  stats/corpus_info.json          collection-level totals
  stats/files/<name>.json         per-.tess statistics (incl. word counts)

Tokenization: whitespace split, stripping edge punctuation but KEEPING the
elision apostrophe U+2019 (it is part of the word, e.g. ἀλλ’). Vocabulary is
counted case-insensitively; lexical diversity follows the referenced post
(words / vocab = mean tokens per type).
"""

import glob
import json
import re
import datetime
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).parent.parent
TEXTS = ROOT / "texts"
STATS = ROOT / "stats"
VERSION = "0.7.0"

# strip edge punctuation; keep U+2019 (elision, part of the word) and letters/marks
STRIP = "…·.,:;!?«»—“”\"'()[]<>‘·*"
TAG = re.compile(r"^<[^>]+>\t?(.*)$")


def tokenize(text: str) -> list[str]:
    return [w for w in (t.strip(STRIP) for t in text.split()) if w]


def work_id(stem: str) -> str:
    return re.sub(r"\.part\..*$", "", stem)


def round4(x: float) -> float:
    return round(x, 4)


def file_stats(path: Path):
    stem = path.name[:-5]
    lines = words = chars = 0
    vocab: Counter = Counter()
    for raw in path.read_text(encoding="utf-8").split("\n"):
        if not raw:
            continue
        m = TAG.match(raw)
        body = m.group(1) if m else raw
        if raw.startswith("<"):
            lines += 1
        toks = tokenize(body)
        words += len(toks)
        chars += len(body)
        for t in toks:
            vocab[t.lower()] += 1
    return stem, lines, words, chars, vocab


def main() -> int:
    meta = {}
    mp = TEXTS / "metadata" / "metadata.json"
    if mp.exists():
        meta = json.loads(mp.read_text(encoding="utf-8"))

    (STATS / "files").mkdir(parents=True, exist_ok=True)
    files = sorted(TEXTS.glob("*.tess"))

    corpus_vocab: Counter = Counter()
    tot_words = tot_lines = tot_chars = 0
    authors, works = set(), set()

    for path in files:
        stem, lines, words, chars, vocab = file_stats(path)
        author = stem.split(".")[0]
        work = work_id(stem)
        md = meta.get(path.name, {})
        entry = {
            "file": path.name,
            "author": author,
            "author_label": md.get("author", ""),
            "work": work,
            "mode": md.get("mode", ""),
            "lines": lines,
            "words": words,
            "vocab": len(vocab),
            "hapax_legomena": sum(1 for c in vocab.values() if c == 1),
            "lexical_diversity": round4(words / len(vocab)) if vocab else 0,
            "words_per_line": round4(words / lines) if lines else 0,
            "chars": chars,
        }
        (STATS / "files" / f"{stem}.json").write_text(
            json.dumps(entry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        corpus_vocab.update(vocab)
        tot_words += words
        tot_lines += lines
        tot_chars += chars
        authors.add(author)
        works.add(work)

    info = {
        "corpus": "CLTK Tesserae Ancient Greek Corpus",
        "version": VERSION,
        "generated": datetime.date.today().isoformat(),
        "files": len(files),
        "authors": len(authors),
        "works": len(works),
        "lines": tot_lines,
        "words": tot_words,
        "vocab": len(corpus_vocab),
        "hapax_legomena": sum(1 for c in corpus_vocab.values() if c == 1),
        "chars": tot_chars,
        "lexical_diversity": round4(tot_words / len(corpus_vocab)) if corpus_vocab else 0,
        "words_per_file": round4(tot_words / len(files)) if files else 0,
        "words_per_line": round4(tot_words / tot_lines) if tot_lines else 0,
    }
    (STATS / "corpus_info.json").write_text(
        json.dumps(info, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"wrote stats/corpus_info.json and {len(files)} per-file summaries under stats/files/")
    for k, v in info.items():
        print(f"    {k}: {v}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
