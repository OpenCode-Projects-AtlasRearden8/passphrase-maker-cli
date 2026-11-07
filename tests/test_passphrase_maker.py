import math
import re
import statistics

import pytest

import passphrase_maker as pm


@pytest.fixture(scope="module")
def real_words():
    return pm.load_words()


def test_load_words_size_and_uniqueness(real_words):
    assert len(real_words) == 7776
    assert len(set(real_words)) == len(real_words)


def test_load_words_entries_are_clean(real_words):
    for word in real_words:
        assert word == word.strip()
        assert " " not in word


def test_load_words_missing_file_raises():
    with pytest.raises(OSError):
        pm.load_words("/no/such/path.txt")

def test_load_words_empty_file_raises(tmp_path):
    empty = tmp_path / "empty.txt"
    empty.write_text("no tab separated entries here\n")
    with pytest.raises(ValueError):
        pm.load_words(empty)


class TestSelectionRandomness:
    def test_word_count_respected(self, real_words):
        for count in (2, 5, 12):
            result = pm.generate(real_words, count, "hyphen")
            words = result.split("-")
            assert len(words) == count

    def test_only_words_from_the_list(self, real_words, monkeypatch):
        words = real_words
        monkeypatch.setattr(pm, "pick_word", lambda _: words[0])
        result = pm.generate(words, 4, "space")
        assert result.split(" ") == [words[0]] * 4

    def test_pick_word_returns_list_members_and_varies(self, real_words):
        results = {pm.pick_word(real_words) for _ in range(500)}
        assert results <= set(real_words)
        assert len(results) > 200

    def test_repeated_calls_differ(self, real_words):
        results = {pm.generate(real_words, 4, "space") for _ in range(60)}
        assert len(results) >= 50

    def test_word_draws_covers_list(self, real_words):
        draws = [pm.pick_word(real_words) for _ in range(2000)]
        distinct = len(set(draws))
        assert distinct > 1500

    def test_word_draws_not_biased_to_first_words(self, real_words):
        draws = [pm.pick_word(real_words) for _ in range(2000)]
        ranks = [real_words.index(word) / len(real_words) for word in draws]
        assert statistics.mean(ranks) == pytest.approx(0.5, abs=0.05)
        assert statistics.stdev(ranks) == pytest.approx(0.289, abs=0.05)

    def test_random_separator_varies(self):
        seen = {pm.pick_separator_char() for _ in range(300)}
        assert seen == set(pm.RANDOM_SEPARATORS)

    def test_named_separators_join(self, real_words):
        expected = {"space": " ", "hyphen": "-", "period": ".", "underscore": "_",
                    "comma": ",", "plus": "+"}
        for name, char in expected.items():
            result = pm.generate(real_words, 3, name)
            parts = result.split(char)
            assert len(parts) == 3
            assert all(part in real_words for part in parts)

    def test_no_separator(self, real_words, monkeypatch):
        sample = [real_words[i] for i in (10, 20, 30)]
        it = iter(sample)
        monkeypatch.setattr(pm, "pick_word", lambda _: next(it))
        result = pm.generate(real_words, 3, "none")
        assert result == "".join(sample)
        assert result != " ".join(sample)


class TestStrengthMath:
    def test_bits_per_word(self, real_words):
        assert pm.entropy_bits(1, len(real_words)) == pytest.approx(12.925, abs=0.001)

    def test_default_six_words(self, real_words):
        assert pm.entropy_bits(6, len(real_words)) == pytest.approx(77.55, abs=0.01)

    def test_extra_word_multiplies_space(self, real_words):
        assert pm.entropy_bits(7, len(real_words)) - pm.entropy_bits(6, len(real_words)) == pytest.approx(math.log2(7776))

    def test_summary_reports_default_bits(self, real_words):
        text = pm.summary(6, len(real_words))
        assert "77.5 bits" in text
        assert "2^78" in text

    def test_summary_lists_threat_rates(self):
        text = pm.summary(6, 7776)
        for line in text.splitlines():
            if "online (throttled)" in line:
                assert "instantly" not in line
            if "offline GPU rig" in line:
                assert re.search(r"\byears\b", line)

    def test_format_seconds_units(self):
        assert pm.format_seconds(0.4) == "instantly"
        assert pm.format_seconds(1) == "1 second"
        assert pm.format_seconds(2) == "2 seconds"
        assert pm.format_seconds(80) == "1 minute"
        assert pm.format_seconds(120) == "2 minutes"
        assert pm.format_seconds(3600) == "1 hour"
        assert pm.format_seconds(86400) == "1 day"
        assert pm.format_seconds(31_557_600) == "1 year"
        assert pm.format_seconds(31_557_600 * 100) == "100 years"
        assert pm.format_seconds(31_557_600 * 2e6) == "2.0 million years"

    def test_summary_scales_with_words(self):
        small = pm.summary(2, 7776)
        big = pm.summary(10, 7776)
        assert "25.8 bits" in small
        assert "129.2 bits" in big

    def test_time_estimates_match_entropy_half_life(self):
        bits = pm.entropy_bits(8, 7776)
        seconds = (2**bits) / 2 / pm.BUILTIN_GUESS_RATES["offline GPU rig"]
        formatted = pm.format_seconds(seconds)
        assert "years" in formatted


def test_cli_outputs_passphrase(real_words, capsys):
    rc = pm.main(["--words", "4", "--quiet"])
    out = capsys.readouterr().out
    assert rc == 0
    words = [w for w in out.split() if w in real_words]
    assert len(words) == 4


def test_cli_default_shows_strength(capsys):
    rc = pm.main([])
    out = capsys.readouterr().out
    assert rc == 0
    assert "77.5 bits" in out
    assert "Strength:" in out


def test_cli_explain_prints_explanation(capsys):
    rc = pm.main(["--explain", "--quiet"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "Why passphrases work" in out


def test_cli_word_count_out_of_range(capsys):
    with pytest.raises(SystemExit):
        pm.main(["--words", "1"])


def test_cli_save_writes_only_when_asked(tmp_path, capsys):
    target = tmp_path / "out.txt"
    assert not target.exists()
    rc = pm.main(["--quiet"])
    assert rc == 0
    capsys.readouterr()
    assert not target.exists()
    rc = pm.main(["--quiet", "--save", str(target)])
    out = capsys.readouterr().out
    assert rc == 0
    assert target.exists()
    assert target.read_text(encoding="utf-8").strip() == out.splitlines()[0]
