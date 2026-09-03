import pytest

from morfoskop.pipeline import TokenInfo
from morfoskop.paradigm_productivity import ParadigmProductivity
from morfoskop.domain_specificity import DomainSpecificity
from morfoskop.register_axis import build_register_axis


def tok(lemma, pos="NOUN", case=None):
    morph = {"Case": case} if case else {}
    return TokenInfo(text=lemma, lemma=lemma, pos=pos, morph=morph)


def test_specialist_lemma_lands_in_specjalistyczny_quadrant():
    # "termin": rare in reference (high keyness), always same case (low
    # entropy) -- the specialist-text pattern per register_axis.py's own
    # rationale.
    target = (
        [tok("termin", case="Nom")] * 5
        + [tok("i")] * 20
    )
    reference = [tok("termin", case="Nom")] * 1 + [tok("i")] * 100

    paradigm = ParadigmProductivity(min_occurrences=3).analyze(target, pos="NOUN")
    keyness = DomainSpecificity(min_freq_target=3).compare(target, reference)

    axis = build_register_axis(paradigm, keyness, min_occurrences=3)
    by_lemma = {p.lemma: p for p in axis.points}

    assert "termin" in by_lemma
    assert by_lemma["termin"].quadrant() == "specjalistyczny"


def test_productive_rare_lemma_lands_in_wyzszy_jezykowo():
    # rare relative to reference (high keyness) AND spread across cases
    # (high entropy) -- the higher-register pattern.
    target = (
        [tok("splendor", case="Nom")]
        + [tok("splendor", case="Gen")]
        + [tok("splendor", case="Ins")]
        + [tok("i")] * 20
    )
    reference = [tok("splendor", case="Nom")] * 1 + [tok("i")] * 100

    paradigm = ParadigmProductivity(min_occurrences=3).analyze(target, pos="NOUN")
    keyness = DomainSpecificity(min_freq_target=1).compare(target, reference)

    axis = build_register_axis(paradigm, keyness, min_occurrences=3)
    by_lemma = {p.lemma: p for p in axis.points}

    assert by_lemma["splendor"].quadrant() == "wyzszy_jezykowo"


def test_mismatched_threshold_raises():
    target = [tok("cokolwiek")] * 5
    paradigm = ParadigmProductivity(min_occurrences=1).analyze(target, pos="NOUN")
    keyness = DomainSpecificity(min_freq_target=1).compare(target, target)

    with pytest.raises(ValueError):
        build_register_axis(paradigm, keyness, min_occurrences=3)


def test_lemma_missing_from_keyness_side_is_dropped_not_zero_filled():
    target = [tok("obecny_tylko_w_paradygmacie")] * 5
    paradigm = ParadigmProductivity(min_occurrences=3).analyze(target, pos="NOUN")
    keyness = []  # nothing eligible on the keyness side

    axis = build_register_axis(paradigm, keyness, min_occurrences=3)
    assert axis.points == []
