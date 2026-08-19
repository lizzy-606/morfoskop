from morfoskop.pipeline import TokenInfo
from morfoskop.domain_specificity import DomainSpecificity


def tok(lemma, pos="NOUN"):
    return TokenInfo(text=lemma, lemma=lemma, pos=pos, morph={})


def test_domain_specific_term_gets_high_g2():
    # "afazja" frequent in the domain (speech therapy), absent from reference
    target = [tok("afazja")] * 10 + [tok("pacjent")] * 5 + [tok("i")] * 20
    reference = [tok("pies")] * 10 + [tok("kot")] * 10 + [tok("i")] * 100

    results = DomainSpecificity(min_freq_target=1).compare(target, reference)
    by_lemma = {r.lemma: r for r in results}

    assert by_lemma["afazja"].direction == "target"
    assert by_lemma["afazja"].g2 > 0
    # "afazja" should have a higher G2 than "i" (frequent in both corpora =
    # not very specific)
    assert by_lemma["afazja"].g2 > by_lemma["i"].g2


def test_min_freq_filters_rare_target_words():
    target = [tok("rzadkie")] * 1 + [tok("pospolite")] * 10
    reference = [tok("cokolwiek")] * 50

    results = DomainSpecificity(min_freq_target=3).compare(target, reference)
    lemmas = {r.lemma for r in results}
    assert "rzadkie" not in lemmas
    assert "pospolite" in lemmas


def test_top_domain_specific_returns_only_target_direction():
    target = [tok("termin")] * 8 + [tok("i")] * 5
    reference = [tok("termin")] * 1 + [tok("i")] * 50

    results = DomainSpecificity(min_freq_target=1).top_domain_specific(target, reference, n=5)
    assert all(r.direction == "target" for r in results)
