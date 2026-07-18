# Changelog

All notable changes to this project will be documented in this file.

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
