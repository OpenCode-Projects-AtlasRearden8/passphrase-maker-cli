# Passphrase Maker

An offline passphrase generator that rolls real dice (cryptographically) using the
EFF large diceware word list. Pick how many words and what goes between them, and
get a passphrase plus an honest estimate of how strong it actually is.

Built by [Asdale Dynamics, LLC](https://dylanasdale.github.io) - plain-English,
step-by-step tools that respect your privacy.

## Why use it

- **Offline.** No network calls, ever. Words come from a bundled file on your disk.
- **Real randomness.** Words are chosen with Python's `secrets` module, which draws
  from your operating system's cryptographic random source - not `random`.
- **Honest math.** It tells you exactly how much strength you're buying (about
  12.9 bits per word) and shows crack-time estimates at three realistic attack
  speeds, including the pessimistic ones.
- **Nothing written to disk** unless you explicitly ask (see `--save`).

## Quick start

Requires Python 3.10 or newer. No packages to install.

```bash
python3 passphrase_maker.py
```

Output:

```
maple cactus violet ribcage gingham oyster

Strength: 6 words x 12.9 bits = 77.5 bits (about 2^78 guesses)
  online (throttled) (100 guesses/sec): 119.0 trillion years (median)
  online (unthrottled) (10,000 guesses/sec): 1.2 trillion years (median)
  offline GPU rig (10,000,000,000 guesses/sec): 1.2 billion years (median)
  ...
```

(Times shown are examples; every run rolls a fresh passphrase.)

## Options

| Flag | What it does |
|---|---|
| `-w, --words N` | Number of words, 2-20 (default 6) |
| `-s, --separator` | `none`, `space`, `hyphen`, `period`, `underscore`, `comma`, `plus`, or `random` (rolls a separator too) |
| `-e, --explain` | Print the plain-English "why passphrases work" explanation |
| `-q, --quiet` | Print only the passphrase, good for piping |
| `--save FILE` | Also write the passphrase to FILE - written only when you ask |
| `--list FILE` | Use a different tab-separated diceware word list |

Examples:

```bash
python3 passphrase_maker.py -w 5 -s hyphen        # cozy-looking-accordion-maple-wren
python3 passphrase_maker.py -w 8 -s random        # 103.4 bits, heavy-duty mode
python3 passphrase_maker.py --explain             # friendly tour of the math
python3 -m pytest tests                           # run the test suite
```

## Why passphrases work (the short version)

Password strength is a guessing game: how many tries would an attacker need?
Rules like "add a symbol" grow that number slowly, and the results are hard to
remember. Random words grow it fast: each word drawn truly at random from this
7,776-word list adds about 12.9 bits, which multiplies the attacker's work by
7,776. Your brain is great at remembering silly scenes ("a cactus riding a
canoe"), so a passphrase buys more strength per memory-cell than a mangled
password ever will.

Two honest caveats, which the tool prints too:

1. You - not the tool - must actually get the randomness. Let the tool pick
   the words; self-chosen words quietly leak length, names, and keyboard habits.
2. Entropy isn't a force field. If a site is breached with weak password
   hashing, or malware watches you type, no password math helps. Pair this
   with a password manager and two-step verification where offered.

## Privacy and safety

- Nothing is sent over the network; the script imports only Python's standard library.
- Nothing is written to disk unless you pass `--save`.
- Passphrases are never logged by the tool; if you pipe them, that's on your shell.

## Tests

```bash
python3 -m pytest tests -v
```

The suite covers selection randomness (word count, list membership, coverage
across draws, separator behavior, no "lucky first words" bias) and the strength
math (entropy per word, crack-time formatting, summary output).

## License

MIT - see [LICENSE](LICENSE). Copyright (c) 2026 Asdale Dynamics, LLC.

Word list: the [EFF Diceware word list](https://www.eff.org/dice) (large list,
7,776 words, tab-separated dice-number format), used as distributed by EFF.

## Credits

Part of the beginner-friendly tool line from Asdale Dynamics, LLC, home of
*The Massive AI Manual* at [dylanasdale.github.io](https://dylanasdale.github.io).
