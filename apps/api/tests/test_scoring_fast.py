# apps/api/tests/test_scoring_fast.py

from app.scoring import words_per_minute, filler_stats


def test_wpm_zero_duration():
    assert words_per_minute("hello world", 0) == 0.0


def test_wpm_basic():
    text = "word " * 150  # 150 words in ~60s => 150 WPM
    assert abs(words_per_minute(text, 60.0) - 150.0) < 1e-6


def test_filler_stats_counts_multiword():
    text = "Um... I was like, you know, actually thinking."
    stats = filler_stats(text)
    # sanity: three different fillers present
    assert stats["counts"]["um"] >= 1
    assert stats["counts"]["like"] >= 1
    assert stats["counts"]["you know"] >= 1
    assert stats["total"] >= 3


def test_filler_word_boundaries():
    # "aluminum" should NOT count "um" (word-boundary check)
    text = "Aluminum is a metal. Um, also, summary isn’t um."
    stats = filler_stats(text)
    # at least the explicit "Um" and "um" should count = 2
    assert stats["counts"]["um"] >= 2
