import math

from morfoskop.pipeline import TokenInfo
from morfoskop.paradigm_productivity import ParadigmProductivity


def tok(text, lemma, pos, **morph):
    return TokenInfo(text=text, lemma=lemma, pos=pos, morph=morph)


def test_productive_lemma_has_high_entropy():
    # "kot" used in five different cases, evenly -> high entropy
    tokens = [
        tok("kot", "kot", "NOUN", Case="Nom"),
        tok("kota", "kot", "NOUN", Case="Gen"),
        tok("kotu", "kot", "NOUN", Case="Dat"),
        tok("kotem", "kot", "NOUN", Case="Ins"),
        tok("kocie", "kot", "NOUN", Case="Loc"),
    ]
    report = ParadigmProductivity(min_occurrences=2).analyze(tokens, pos="NOUN")
    stats = report.lemma_stats["kot"]
    assert stats.distinct_cells == 5
    assert stats.normalized_entropy == 1.0  # perfectly even distribution


def test_repetitive_lemma_has_zero_entropy():
    # "pies" five times in the same case -> zero entropy, zero productivity
    tokens = [tok("psa", "pies", "NOUN", Case="Gen") for _ in range(5)]
    report = ParadigmProductivity(min_occurrences=2).analyze(tokens, pos="NOUN")
    stats = report.lemma_stats["pies"]
    assert stats.distinct_cells == 1
    assert stats.normalized_entropy == 0.0


def test_stylometrix_style_frequency_would_be_identical_here():
    """Control test for the README thesis: two texts with identical
    Case=Gen frequency (StyloMetrix would not tell them apart), but
    different paradigm productivity (morfoskop tells them apart)."""
    # Text A: one lemma, genitive repeated 4 times
    text_a = [tok("psa", "pies", "NOUN", Case="Gen") for _ in range(4)]
    # Text B: four different lemmas, each once in the genitive
    text_b = [
        tok("psa", "pies", "NOUN", Case="Gen"),
        tok("kota", "kot", "NOUN", Case="Gen"),
        tok("stołu", "stół", "NOUN", Case="Gen"),
        tok("domu", "dom", "NOUN", Case="Gen"),
    ]

    analyzer = ParadigmProductivity(min_occurrences=1)
    report_a = analyzer.analyze(text_a, pos="NOUN")
    report_b = analyzer.analyze(text_b, pos="NOUN")

    # Case=Gen frequency / len(doc) is identical in both (4/4 = 1.0) — this
    # is what StyloMetrix would see. But these are two different
    # phenomena: A is one lemma looping, B is four different lemmas in the
    # same cell.
    freq_gen_a = sum(1 for t in text_a if t.morph.get("Case") == "Gen") / len(text_a)
    freq_gen_b = sum(1 for t in text_b if t.morph.get("Case") == "Gen") / len(text_b)
    assert freq_gen_a == freq_gen_b == 1.0

    # morfoskop tells them apart at the level of lemma count and individual
    # entropy
    assert len(report_a.lemma_stats) == 1
    assert len(report_b.lemma_stats) == 4
    assert report_a.lemma_stats["pies"].normalized_entropy == 0.0


def test_verb_cell_uses_tense_mood_aspect():
    tokens = [
        tok("robię", "robić", "VERB", Tense="Pres", Mood="Ind", Aspect="Imp"),
        tok("robiłem", "robić", "VERB", Tense="Past", Mood="Ind", Aspect="Imp"),
        tok("zrobię", "robić", "VERB", Tense="Fut", Mood="Ind", Aspect="Imp"),
    ]
    report = ParadigmProductivity(min_occurrences=1).analyze(tokens, pos="VERB")
    stats = report.lemma_stats["robić"]
    assert stats.distinct_cells == 3
    assert stats.coverage is None  # undefined for verbs


def test_coverage_for_nouns_bounded_0_1():
    tokens = [tok("dom", "dom", "NOUN", Case="Nom")]
    report = ParadigmProductivity(min_occurrences=1).analyze(tokens, pos="NOUN")
    stats = report.lemma_stats["dom"]
    assert 0.0 <= stats.coverage <= 1.0
    assert math.isclose(stats.coverage, 1 / 7)
