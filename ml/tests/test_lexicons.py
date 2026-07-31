"""Regression tests for the word-boundary lexicon matcher.

_count_hits/_lexicon_pattern is the foundation every psychology/urgency/
threat/etc. feature is built on — a bug here silently corrupts ~20 features
at once. This locks in the real "now" vs "know" false-positive bug found
by testing earlier in the project.
"""

from features.lexicons import URGENCY_WORDS, THREAT_WORDS, _count_hits


def test_substring_inside_unrelated_word_is_not_a_hit():
    # "now" must not match inside "know"/"known" — the real bug this
    # word-boundary matching was added to fix.
    assert _count_hits("i know him well", URGENCY_WORDS) == 0
    assert _count_hits("as is well known", URGENCY_WORDS) == 0


def test_whole_word_hit_is_counted():
    assert _count_hits("do this now", URGENCY_WORDS) == 1


def test_case_insensitivity_is_the_callers_responsibility():
    # _count_hits expects already-lowercased text (callers lowercase before
    # calling it) -- verify the pattern itself is case-sensitive so a caller
    # that forgets to lowercase fails loudly instead of silently undercounting.
    assert _count_hits("NOW", URGENCY_WORDS) == 0
    assert _count_hits("now", URGENCY_WORDS) == 1


def test_multi_word_phrase_matches():
    assert _count_hits("this is your final notice", URGENCY_WORDS) == 1


def test_multiple_distinct_hits_counted_separately():
    text = "your account will be suspended and blocked"
    assert _count_hits(text, THREAT_WORDS) == 2


def test_no_hits_returns_zero_not_error():
    assert _count_hits("just a normal friendly message", URGENCY_WORDS) == 0
    assert _count_hits("", URGENCY_WORDS) == 0
