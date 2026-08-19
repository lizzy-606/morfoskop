"""
Inflectional paradigm productivity.

Difference from StyloMetrix (the "Inflection" category):
StyloMetrix counts feature frequency per token: ratio(count(Case=Gen), len(doc)).
It answers "how much of the text is in the genitive".

Here the question is different: "for a given lexeme, how many distinct
paradigm cells were actually used in the text, and how evenly". It answers
a question about generative language use — whether the author/model moves
across the paradigm, or loops on a single form.

Grounding: Ackerman & Malouf (2013) "Morphological Organization: The Low
Conditional Entropy Conjecture", Language 89(3) — entropy as a measure of
predictability/productivity of paradigm cells. Baayen (1992) — type/token
ratio as a classic estimator of morphological productivity.
"""

from __future__ import annotations

import math
from collections import Counter, defaultdict
from dataclasses import dataclass, field

from .pipeline import TokenInfo

# The seven Polish cases. Vocative can be marginal in written text — it
# stays in the set deliberately: its absence is itself a signal (formal
# written register rarely generates it), not a measurement error.
POLISH_CASES = ("Nom", "Gen", "Dat", "Acc", "Ins", "Loc", "Voc")

# Verbal paradigm axes considered. Deliberately not the full combinatorics
# (aspect x tense x mood x person x number x gender would give hundreds of
# theoretical cells, most of them empty for grammatical, not stylistic,
# reasons — e.g. past tense does not cross with imperative mood). We take
# (Tense, Mood, Aspect) as a sensible, interpretable cross-section.
VERB_AXES = ("Tense", "Mood", "Aspect")


@dataclass
class LemmaParadigmStats:
    lemma: str
    pos: str
    occurrences: int
    cells: Counter  # e.g. Counter({('Nom',): 3, ('Gen',): 1})

    @property
    def distinct_cells(self) -> int:
        return len(self.cells)

    @property
    def coverage(self) -> float | None:
        """Coverage against the theoretical cell set — only for nouns/
        adjectives, where the set (7 cases) is unambiguous. Returns None
        for verbs, since the theoretical size depends on the lexeme's
        aspect."""
        if self.pos not in ("NOUN", "PROPN", "ADJ"):
            return None
        return self.distinct_cells / len(POLISH_CASES)

    @property
    def entropy(self) -> float:
        """Shannon entropy of usage distribution across cells. 0 = the
        lexeme is always in the same form (zero productivity visible in
        the text), max = log2(n) with n attested cells used evenly."""
        total = sum(self.cells.values())
        if total == 0:
            return 0.0
        h = 0.0
        for count in self.cells.values():
            p = count / total
            h -= p * math.log2(p)
        return h

    @property
    def normalized_entropy(self) -> float:
        """Entropy divided by log2(distinct_cells) — 0..1, comparable
        across lemmas with different numbers of attested cells. 1 = maximally
        even distribution of usage, 0 or undefined when only one cell."""
        if self.distinct_cells <= 1:
            return 0.0
        return self.entropy / math.log2(self.distinct_cells)


@dataclass
class ParadigmProductivityReport:
    pos: str
    lemma_stats: dict[str, LemmaParadigmStats]
    min_occurrences: int

    def eligible(self) -> list[LemmaParadigmStats]:
        """Lemmas with occurrence count >= threshold — below the threshold,
        entropy and coverage are unreliable (a lemma used once necessarily
        has distinct_cells=1)."""
        return [s for s in self.lemma_stats.values() if s.occurrences >= self.min_occurrences]

    def mean_coverage(self) -> float | None:
        vals = [s.coverage for s in self.eligible() if s.coverage is not None]
        return sum(vals) / len(vals) if vals else None

    def mean_normalized_entropy(self) -> float | None:
        vals = [s.normalized_entropy for s in self.eligible()]
        return sum(vals) / len(vals) if vals else None

    def top_productive(self, n: int = 10) -> list[LemmaParadigmStats]:
        return sorted(self.eligible(), key=lambda s: s.normalized_entropy, reverse=True)[:n]

    def top_repetitive(self, n: int = 10) -> list[LemmaParadigmStats]:
        """Lemmas used repeatedly, but nearly always in the same form —
        candidates for a generative 'loop'."""
        candidates = [s for s in self.eligible() if s.occurrences >= max(3, self.min_occurrences)]
        return sorted(candidates, key=lambda s: s.normalized_entropy)[:n]


class ParadigmProductivity:
    def __init__(self, min_occurrences: int = 2):
        self.min_occurrences = min_occurrences

    def _cell_for_token(self, token: TokenInfo) -> tuple[str, ...] | None:
        if token.pos in ("NOUN", "PROPN", "ADJ"):
            case = token.morph.get("Case")
            return (case,) if case else None
        if token.pos in ("VERB", "AUX"):
            cell = tuple(token.morph.get(axis, "?") for axis in VERB_AXES)
            return cell if any(v != "?" for v in cell) else None
        return None

    def analyze(self, tokens: list[TokenInfo], pos: str) -> ParadigmProductivityReport:
        by_lemma: dict[str, Counter] = defaultdict(Counter)
        occurrences: Counter = Counter()

        for token in tokens:
            if token.pos != pos:
                continue
            cell = self._cell_for_token(token)
            occurrences[token.lemma] += 1
            if cell is not None:
                by_lemma[token.lemma][cell] += 1

        lemma_stats = {
            lemma: LemmaParadigmStats(
                lemma=lemma, pos=pos, occurrences=occurrences[lemma], cells=cells
            )
            for lemma, cells in by_lemma.items()
        }
        # Lemmas that occurred but yielded no recognized cell (missing/
        # incomplete morph) are kept out of the report — this is a data
        # quality signal, not lack of productivity; worth separate logging
        # in practice.
        return ParadigmProductivityReport(
            pos=pos, lemma_stats=lemma_stats, min_occurrences=self.min_occurrences
        )

    def analyze_all(
        self, tokens: list[TokenInfo], pos_list: tuple[str, ...] = ("NOUN", "ADJ", "VERB")
    ) -> dict[str, ParadigmProductivityReport]:
        return {pos: self.analyze(tokens, pos) for pos in pos_list}
