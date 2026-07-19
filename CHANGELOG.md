# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- Wireframe `texts/metadata/metadata.json` (per-file metadata, keyed by `.tess` filename; matches the Latin corpus's metadata location and CLTK Readers convention). Extended authority-ready schema — `author`, `title`, `date`, `genre`, `mode`, `wikidata`, `tlg_author`, `tlg_work`, `edition` — with empty values pending population from local/Tesserae metadata and Wikidata/TLG lookups. Exact 1:1 coverage with the 923 text files.

## [0.5.1] - 2026-07-19

### Fixed
- Repaired mojibake quotation marks: 96 stray C1 control characters (`U+009C`/`U+009D`) — the corrupted tails of the corpus's curly quotes `“` / `”` — restored to `U+201C` / `U+201D` in Pindar and Theocritus (opening/closing direct speech). Consistent with the sibling Latin corpus's policy of preserving legitimate curly quotes and repairing mojibake to its intended Unicode rather than straightening.
- Removed 73 stray `U+FEFF` (zero-width no-break space) artifacts from 4 files (Aelian, Demetrius, Philostratus).

## [0.5] - 2026-07-19

### Fixed
- Removed non-Greek editorial contamination from 54 lines (Libanius, Gregory of Nazianzus, Polybius, Arrian) that had bled in from scanned critical editions:
  - Excised Latin editorial rubrics/argumenta and running page-headers (Foerster edition) interleaved in the Libanius declamations and orations.
  - Removed edition page/reference markers (Reiske, Morell, Sieber, Boissonade) inserted mid-text, rejoining the Greek words they had split (e.g. `φθοR III 337 ρὰν` → φθορὰν; `ἈκαMor δημίαν` → Ἀκαδημίαν).
  - Excised English translation glosses that had crept into Gregory's *Theological Orations*.
  - Corrected OCR errors where Greek had been rendered in Latin script (`co`/`cb`/`ob` → ὦ, `Mr` → μή, `iva` → ἵνα, `pous` → -ρους) and dittographies (`γείγείτων` → γείτων, `τεττίτεττίγων` → τεττίγων).
  - Deleted a transliterated apparatus note in Polybius; removed stray `#x003E;` entity artifacts.
  - Split two Arrian sections (*Anab.* 7.24.1–2) that had been merged into a single line.
- Known remaining: 5 severely-mangled Libanius lines whose base text is entangled with apparatus criticus await reconstruction against Foerster; pure-Greek OCR errors in Libanius are not yet systematically addressed.

## [0.4] - 2026-07-18

### Changed
- Split the remaining bundled multi-book `.tess` files into one file per book, so the whole corpus now follows the one-file-per-book convention used by the Iliad, Odyssey, and Quintus Smyrnaeus:
  - Nonnus, *Dionysiaca*: 5 bundled "decade" files (books 1–10, 11–20, 21–30, 31–40, 41–48) → 48 per-book files (`part.1`…`part.48`).
  - Dionysius of Halicarnassus, *Antiquitates Romanae*: the `part.12.books_12-20` bundle → per-book files (`part.12`…`part.20`). Books 17–18 survive only as jointly-transmitted excerpts (every citation is tagged `17-18.x.y`) and are kept together as `part.17-18.tess`.
  - Both splits verified byte-identical: concatenating the per-book files in order reproduces the original bundles exactly.
- Normalized trailing newlines: added a single final newline to the 120 files that lacked one. Whitespace-only, verified with no change to textual content.

### Added
- Citation-format validator (`utils/validate_tess.py`) and a GitHub Actions workflow that runs it on every push and pull request to `main`. The corpus passes with zero violations across all files.

## [0.3] - 2022-01-28

### Added
- Added the Homeric Hymns; corpus texts refreshed.

## [0.1] - 2018-12-12

### Added
- Initial release of the CLTK / LatinCy fork of the Tesserae Ancient Greek corpus, with README, license, and citation metadata for use with the Classical Language Toolkit and LatinCy NLP pipelines.

<!-- Detailed history prior to v0.4 predates this changelog; see git history. -->
