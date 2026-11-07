# STATUS.md - passphrase-maker-cli

## What was built

A fully offline passphrase generator CLI (`passphrase_maker.py`) plus a bundled
copy of the EFF large diceware word list (7,776 words, downloaded once from
eff.org during development; no part of the tool touches the network at runtime).

Features:

- Word count selection (2-20 words, default 6 - about 77.5 bits of entropy).
- Separator styles: `none`, `space`, `hyphen`, `period`, `underscore`, `comma`,
  `plus`, or `random` (rolls a separator with the same crypto RNG).
- Real randomness: every word comes from Python's `secrets` module
  (`secrets.randbelow`), i.e. the OS cryptographic random source.
- Honest strength estimates: total entropy in bits plus median crack-time at
  three attack rates (throttled online 100 g/s, unthrottled online 10k g/s,
  offline GPU rig 10B g/s), with explicit caveats that the math assumes the
  word list is known and that real-world safety also depends on hashing,
  phishing, and malware.
- Friendly `--explain` mode: a plain-English "why passphrases work" tour,
  including the two honest caveats (self-chosen words leak, entropy is not a
  force field).
- Privacy posture: standard library only, no network calls, nothing written to
  disk unless `--save FILE` is explicitly passed.
- Alternate word lists supported via `--list` (tab-separated diceware format).
- README.md (with Asdale Dynamics, LLC credit) and MIT LICENSE
  ("Copyright (c) 2026 Asdale Dynamics, LLC").

## How to run it

```bash
python3 passphrase_maker.py                 # 6 words, spaces, strength summary
python3 passphrase_maker.py -w 5 -s hyphen  # 5 words joined with hyphens
python3 passphrase_maker.py --explain       # include the why-it-works tour
python3 passphrase_maker.py -q --save f.txt # passphrase only, also saved to file
```

Requires Python 3.10+; no third-party dependencies.

## Verification results

- `python3 -m pytest tests -v`: **26 passed** (pytest 9.1.1, Python 3.13.5).
- Coverage includes:
  - Selection randomness: word count respected, only list members chosen,
    repeated calls differ (60 runs -> 50+ distinct), 2000 draws cover
    1500+ distinct words, draw rank distribution is centered/uniform
    (mean ~0.5, stdev ~0.289), random separator hits all six of its choices,
    named separators join correctly, `none` joins in pick order.
  - Strength math: 12.925 bits/word, 77.5 bits for the 6-word default,
    each extra word adds exactly log2(7776), crack-time formatting across
    seconds/minutes/hours/days/years/millions-of-years, summary text asserts.
  - CLI behavior: quiet mode, default summary rendering, `--explain`,
    out-of-range word count rejected, `--save` writes only when asked and
    matches the printed passphrase.
- Manual smoke tests of `--help`, plain run, hyphen/random separators, and
  `--explain` all behaved as intended.

## Known gaps

- The estimates say "median", not minimum/maximum, and ignore the astronomically
  small chance of repeated words (which only slightly reduces entropy; noted
  nowhere explicitly - negligible for 6+ words from 7,776).
- No non-English word lists bundled; `--list` accepts any tab-separated
  diceware file, but none ship with the tool.
- No clipboard integration and no `xkcd`-style phrase visualization.
- Word list authorship is EFF's (used under their guidance); the list itself is
  redistributed in tab-separated form with dice numbers preserved.
- No packaging (pyproject entry point); running via `python3 passphrase_maker.py`
  is the supported path for now.
