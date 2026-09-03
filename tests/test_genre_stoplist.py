from morfoskop.pipeline import TokenInfo
from morfoskop.genre_stoplist import is_genre_formula, filter_genre_formulas


def tok(text, lemma=None, pos="NOUN"):
    return TokenInfo(text=text, lemma=lemma or text, pos=pos, morph={})


def test_instruction_lemma_is_flagged():
    assert is_genre_formula(tok("odpowiedź")) is True
    assert is_genre_formula(tok("wskaż", lemma="wskazać", pos="VERB")) is True


def test_domain_term_is_not_flagged():
    assert is_genre_formula(tok("nerka")) is False
    assert is_genre_formula(tok("zapalenie")) is False


def test_option_letter_is_flagged_by_surface_form():
    for letter in "ABCDEabcde":
        assert is_genre_formula(tok(letter, lemma=letter)) is True
    # two-letter tokens are real words, not option labels
    assert is_genre_formula(tok("ab", lemma="ab")) is False


def test_three_digit_enumeration_is_flagged():
    assert is_genre_formula(tok("1,2,3", lemma="1,2,3")) is True
    assert is_genre_formula(tok("2,3,5", lemma="2,3,5")) is True


def test_two_digit_pattern_is_not_flagged_decimal_ambiguity():
    # "3,5" could be an answer combination ("A i C") or a decimal value
    # (a dosage, a lab result, e.g. "3,5 mmol/l") -- deliberately NOT
    # flagged; see comment in genre_stoplist.py on why false negatives are
    # preferred over deleting real clinical numbers.
    assert is_genre_formula(tok("3,5", lemma="3,5")) is False


def test_filter_genre_formulas_drops_only_flagged_tokens():
    tokens = [tok("nerka"), tok("odpowiedź"), tok("B", lemma="B"), tok("zapalenie")]
    kept = filter_genre_formulas(tokens)
    assert [t.text for t in kept] == ["nerka", "zapalenie"]
