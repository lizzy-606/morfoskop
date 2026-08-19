"""
Domain specificity (specialist vocabulary) without a terminology dictionary.

Method: log-likelihood ratio ("keyness"), Dunning (1993) "Accurate Methods
for the Statistics of Surprise and Coincidence", Computational Linguistics
19(1); application to keyness in corpus linguistics: Rayson & Garside
(2000) "Comparing corpora using frequency profiling", WCC@ACL.

Why not a dictionary: for specialist Polish there is no good resource
beyond the 2015 frequency dictionary (which measures exponents, not primes
— a gap documented separately). Instead of depending on a resource that
doesn't exist, the method compares two corpora: lemma frequency in the
target domain vs. a reference corpus. High G2 combined with higher target
frequency signals specificity, without needing any pre-existing term list.
"""

from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass

from .pipeline import TokenInfo


@dataclass
class KeynessResult:
    lemma: str
    freq_target: int
    freq_reference: int
    total_target: int
    total_reference: int
    g2: float
    direction: str  # "target" (over-represented in the domain) or "reference"

    @property
    def rel_freq_target(self) -> float:
        return self.freq_target / self.total_target if self.total_target else 0.0

    @property
    def rel_freq_reference(self) -> float:
        return self.freq_reference / self.total_reference if self.total_reference else 0.0

    def significant(self, threshold: float = 3.84) -> bool:
        """Default threshold 3.84 ~ p<0.05 for df=1 (chi-square). This is a
        rough heuristic from the keyness literature, not a claim of a
        properly calibrated statistical test — with large corpora almost
        everything comes out 'significant', so treat this as a coarse
        filter, not a verdict."""
        return self.g2 >= threshold


class DomainSpecificity:
    def __init__(self, min_freq_target: int = 3):
        self.min_freq_target = min_freq_target

    @staticmethod
    def _lemma_counts(tokens: list[TokenInfo]) -> Counter:
        return Counter(t.lemma for t in tokens)

    def compare(
        self, target_tokens: list[TokenInfo], reference_tokens: list[TokenInfo]
    ) -> list[KeynessResult]:
        target_counts = self._lemma_counts(target_tokens)
        reference_counts = self._lemma_counts(reference_tokens)

        total_target = sum(target_counts.values())
        total_reference = sum(reference_counts.values())

        results = []
        vocabulary = {
            lemma
            for lemma, count in target_counts.items()
            if count >= self.min_freq_target
        }

        for lemma in vocabulary:
            a = target_counts[lemma]
            b = reference_counts.get(lemma, 0)
            g2 = self._log_likelihood(a, b, total_target, total_reference)
            direction = (
                "target"
                if (a / total_target) >= (b / total_reference if total_reference else 0)
                else "reference"
            )
            results.append(
                KeynessResult(
                    lemma=lemma,
                    freq_target=a,
                    freq_reference=b,
                    total_target=total_target,
                    total_reference=total_reference,
                    g2=g2,
                    direction=direction,
                )
            )

        return sorted(results, key=lambda r: r.g2, reverse=True)

    @staticmethod
    def _log_likelihood(a: int, b: int, total_a: int, total_b: int) -> float:
        """G2, the Dunning/Rayson-Garside variant. a, b = absolute
        frequencies of the lemma in the target and reference corpora;
        total_a, total_b = corpus sizes in tokens."""
        if total_a == 0 or total_b == 0:
            return 0.0

        c = total_a
        d = total_b
        e1 = c * (a + b) / (c + d)
        e2 = d * (a + b) / (c + d)

        g2 = 0.0
        for observed, expected in ((a, e1), (b, e2)):
            if observed > 0 and expected > 0:
                g2 += observed * math.log(observed / expected)
        return 2 * g2

    def top_domain_specific(
        self,
        target_tokens: list[TokenInfo],
        reference_tokens: list[TokenInfo],
        n: int = 20,
    ) -> list[KeynessResult]:
        results = self.compare(target_tokens, reference_tokens)
        return [r for r in results if r.direction == "target"][:n]
