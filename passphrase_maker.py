#!/usr/bin/env python3
"""Offline passphrase generator.

Picks words from a bundled diceware-style word list using the operating
system's cryptographic random source (the `secrets` module). Nothing is
written to disk and no network connection is made unless you pass
--save.
"""

import argparse
import math
import secrets
import sys
from pathlib import Path

WORDLIST_PATH = Path(__file__).resolve().parent / "wordlists" / "eff_large_wordlist.txt"

SEPARATOR_NAMES = ("none", "space", "hyphen", "period", "underscore", "comma", "plus", "random")
SEPARATOR_CHARS = {
    "space": " ",
    "hyphen": "-",
    "period": ".",
    "underscore": "_",
    "comma": ",",
    "plus": "+",
}
RANDOM_SEPARATORS = ("-", ".", "_", " ", "+", ",")

DEFAULT_WORDS = 6
MIN_WORDS = 2
MAX_WORDS = 20

BUILTIN_GUESS_RATES = {
    "online (throttled)": 100,
    "online (unthrottled)": 10_000,
    "offline GPU rig": 10_000_000_000,
}
SECONDS_PER_YEAR = 31_557_600


def load_words(path: Path | str = WORDLIST_PATH) -> list[str]:
    text = Path(path).read_text(encoding="utf-8")
    words = [line.split("\t")[1].strip() for line in text.splitlines() if "\t" in line]
    if not words:
        raise ValueError(f"word list at {path} is empty or malformed")
    if len(set(words)) != len(words):
        raise ValueError(f"word list at {path} contains duplicate words")
    return words


def pick_word(words: list[str]) -> str:
    return words[secrets.randbelow(len(words))]


def pick_separator_char() -> str:
    return RANDOM_SEPARATORS[secrets.randbelow(len(RANDOM_SEPARATORS))]


def generate(words: list[str], count: int, separator: str = "space") -> str:
    if separator == "random":
        joiner = pick_separator_char()
    else:
        joiner = SEPARATOR_CHARS.get(separator, "")
    return joiner.join(pick_word(words) for _ in range(count))


def entropy_bits(count: int, list_size: int) -> float:
    return count * math.log2(list_size)


def format_seconds(seconds: float) -> str:
    if seconds < 1:
        return "instantly"
    minutes = seconds / 60
    hours = seconds / 3600
    days = seconds / 86400
    years = seconds / SECONDS_PER_YEAR
    if minutes < 1:
        return _plural(max(1, round(seconds)), "second")
    if hours < 1:
        return _plural(round(minutes), "minute")
    if days < 1:
        return _plural(round(hours), "hour")
    if years < 1:
        return _plural(round(days), "day")
    if years < 1_000_000:
        return _plural(_human_number(years), "year")
    return f"{_human_number(years)} years"


def _plural(number: str | int, unit: str) -> str:
    number = str(number)
    if number == "1":
        return f"{number} {unit}"
    return f"{number} {unit}s"


def _human_number(value: float) -> str:
    for threshold, label in ((1e12, "trillion"), (1e9, "billion"), (1e6, "million")):
        if value >= threshold:
            return f"{value / threshold:.1f} {label}"
    return f"{value:,.0f}"


def summary(count: int, list_size: int) -> str:
    bits = entropy_bits(count, list_size)
    lines = [
        f"Strength: {count} words x {_bits_per_word(list_size)} bits = {bits:.1f} bits "
        f"(about 2^{int(round(bits))} guesses)",
    ]
    for label, rate in BUILTIN_GUESS_RATES.items():
        seconds = (2**bits) / 2 / rate
        lines.append(f"  {label} ({rate:,} guesses/sec): {format_seconds(seconds)} (median)")
    lines.append("  Assumes the attacker knows this exact word list and is guessing offline.")
    lines.append("  Real-world safety also depends on the site hashing passwords well, and on")
    lines.append("  you never typing this into a phishing page. Math is honest, humans are tricky.")
    return "\n".join(lines)


def _bits_per_word(list_size: int) -> str:
    bits = math.log2(list_size)
    return f"{bits:.1f}"


EXPLANATION = """Why passphrases work (the friendly version)

  Password strength is just a guessing-game: how many tries would an
  attacker need? A typical "strong-looking" password like Tr0ub4dor&3
  has maybe 30-40 bits of entropy, and humans forget those rules fast.

  Now look at what your brain is actually good at: remembering pictures
  and stories. "maple-cactus-violet-ribcage" is four words - silly
  enough to picture as a scene - and words chosen truly at random from
  a 7,776-word list carry about 12.9 bits each. Four words = 51.7 bits.
  Six words = 77.5 bits. Eight = 103.4 bits.

  Each extra word multiplies the guessing space by 7,776. That is a
  lever bigger than any password rule about capitals or 1s-for-ls.

  Two honest caveats:
    1. Randomness matters. "correct horse battery staple" is strong
       only because diceware chose it; if you pick the words yourself,
       English quirks quietly cut the strength. That is why this tool
       rolls the dice for you with a cryptographic random generator.
    2. Entropy is not magic. If a site gets breached with unsalted,
       fast hashes, or if malware watches you type, no password math
       protects you. A password manager plus these passphrases (and
       two-step verification where offered) is the full recipe.

  Bottom line: a few random words are easy to remember out loud, hard
  to guess, and survive password rules that strip symbols. That is why
  security folks have trusted this trick since the 1990s."""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="passphrase_maker",
        description="Offline passphrase generator using a bundled diceware word list.",
    )
    parser.add_argument(
        "-w", "--words",
        type=int, default=DEFAULT_WORDS,
        metavar="N",
        help=f"number of words to use, {MIN_WORDS}-{MAX_WORDS} (default {DEFAULT_WORDS})",
    )
    parser.add_argument(
        "-s", "--separator",
        choices=SEPARATOR_NAMES,
        default="space",
        help="character between words (default 'space'; 'random' rolls a separator too)",
    )
    parser.add_argument(
        "-e", "--explain",
        action="store_true",
        help="print the why-passphrases-work explanation",
    )
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="print only the passphrase (good for piping)",
    )
    parser.add_argument(
        "--save",
        metavar="FILE",
        default=None,
        help="also write the passphrase to FILE (nothing is written unless you ask)",
    )
    parser.add_argument(
        "--list",
        default=WORDLIST_PATH,
        metavar="FILE",
        help="alternate word list file (tab-separated diceware format)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not MIN_WORDS <= args.words <= MAX_WORDS:
        parser.error(f"--words must be between {MIN_WORDS} and {MAX_WORDS}")

    try:
        words = load_words(Path(args.list))
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    passphrase = generate(words, args.words, args.separator)

    if args.explain:
        print(EXPLANATION)
        print()

    print(passphrase)
    if not args.quiet:
        print()
        print(summary(args.words, len(words)))

    if args.save is not None:
        try:
            Path(args.save).write_text(passphrase + "\n", encoding="utf-8")
        except OSError as exc:
            print(f"error: could not save: {exc}", file=sys.stderr)
            return 1
        print(f"\nSaved to {args.save}. Remember to delete it when you are done.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
