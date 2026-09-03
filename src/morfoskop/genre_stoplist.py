"""
Genre-structural stoplist for exam-format text.

Why this exists: keyness (domain_specificity.py) and paradigm productivity
(paradigm_productivity.py) both compute statistics over lemmas — but
multiple-choice exam questions carry a second signal that has nothing to do
with domain or register: the instruction language of the question itself
("wskaż prawidłową odpowiedź", "wymień objawy") and the mechanical residue
of answer options (single-letter labels, digit-enumeration combinations
like "1,2,3"). Verified empirically on speakleash/PES-2018-2022
(choroby_wewnetrzne, 200 questions, vs. a 50-article wikimedia/wikipedia
pl reference): the lemma "odpowiedź" scores the highest G2 in the entire
corpus (370.26) — higher than every genuine medical term, including
"zapalenie" (303.31) and "nerka" (203.53). Left unfiltered, this
genre-structural signal dominates both paradigm productivity and keyness
and gets read as "specialist vocabulary" or "restricted register", which
it is not — it's an artifact of the source's document format.

This is a closed, enumerable set — exam-instruction language does not grow
the way domain terminology does — so a dictionary/stoplist is the correct
tool here (contrast domain_specificity.py's own README note on why open-
class domain terminology is NOT handled with a dictionary; this is the
closed-class case where that objection doesn't apply, the same way
StyloMetrix's `vulgarisms`/`errors` lists are a reasonable closed-set
approach for what they cover).

Not claimed exhaustive. Built from one exam source (PES-2018-2022); a
different exam format will use different instruction phrasing — extend
EXAM_INSTRUCTION_LEMMAS per corpus rather than assuming this list transfers.
"""

from __future__ import annotations

import re

from .pipeline import TokenInfo

# Instruction / correctness-framing vocabulary of Polish multiple-choice exam
# questions. Lemma-level, lowercase.
EXAM_INSTRUCTION_LEMMAS = frozenset({
    "odpowiedź",
    "prawidłowy",
    "prawdziwy",
    "fałszywy",
    "wskazać",
    "wskaż",
    "wymienić",
    "dotyczyć",
    "stwierdzenie",
    "poniższy",
    "powyższy",
    "wyjątek",
    "należeć",
})

# Single-letter answer-option labels (A-E) and digit-enumeration combinations
# ("1,2,3", "2,3,5") — matched against the surface form, not the lemma, since
# these aren't real lexical items to begin with.
#
# Requires >= 3 comma-separated digits deliberately: Polish uses a comma as
# the decimal separator, so a 2-digit pattern like "3,5" is ambiguous between
# an answer-combination ("A i C") and a real decimal value (a dosage, a lab
# result). Erring toward NOT flagging 2-digit patterns means some genuine
# enumeration residue slips through unfiltered, but a missed noise token is
# cheaper than silently deleting a real clinical number from the corpus.
_OPTION_LETTER = re.compile(r"^[a-eA-E]$")
_DIGIT_ENUMERATION = re.compile(r"^\d(,\d){2,}$")


def is_genre_formula(token: TokenInfo) -> bool:
    """True if a token is exam-instruction language or answer-option residue
    rather than content that should count toward domain or register
    statistics."""
    if token.lemma.lower() in EXAM_INSTRUCTION_LEMMAS:
        return True
    if _OPTION_LETTER.match(token.text):
        return True
    if _DIGIT_ENUMERATION.match(token.text):
        return True
    return False


def filter_genre_formulas(tokens: list[TokenInfo]) -> list[TokenInfo]:
    """Drop genre-formula tokens from a token list. Non-destructive: returns
    a new list. Pass the result to ParadigmProductivity.analyze(...) or
    DomainSpecificity.compare(...) in place of the raw token list — this
    module does not modify either of those; it's a pre-filtering step."""
    return [t for t in tokens if not is_genre_formula(t)]
