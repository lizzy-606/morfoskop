"""
Register axis: cross paradigm productivity (entropy) with domain specificity
(keyness) into a single classification space.

Why a third module, not a change to the other two: paradigm_productivity.py
and domain_specificity.py measure two independent things on purpose (see
README's "How this differs from StyloMetrix" — the whole point of morfoskop
is keeping frequency and productivity apart, which is exactly the confound
StyloMetrix's Inflection category is criticized for making). This module
composes their *outputs* after the fact; it does not touch either module's
internals, and neither module needs to know this one exists.

Why entropy or keyness alone can't tell registers apart:

- colloquial speech: common vocabulary (low keyness) + restricted paradigm
  use (low entropy) — a handful of frequently-repeated forms.
- specialist text: domain-marked vocabulary (high keyness) + ALSO
  restricted paradigm use (low entropy) — terminology tends to surface in
  one or two canonical forms (nominative, sometimes genitive), not spread
  across the full case system. Verified empirically: in PES-2018-2022,
  medical terms like "nerka" and "zapalenie" score high G2 while showing
  the same low-entropy, single-form-dominant pattern as ordinary repeated
  words.
- higher-register/literary text: domain-marked-ish or rare vocabulary
  (moderate-to-high keyness) + high entropy — the one register that
  actually exploits the productive paradigm rather than looping on one
  form.

Entropy by itself conflates specialist and colloquial (both score low).
This module crosses it with the frequency axis from keyness to pull them
apart.

Population-threshold note: paradigm_productivity.py and domain_specificity.py
have independently-set eligibility thresholds (min_occurrences,
min_freq_target). Joining their outputs without reconciling those first
means the two measures are computed over different lemma populations —
that's sampling noise, not signal. build_register_axis() takes one
min_occurrences and enforces it on both sides before joining; it raises
rather than silently reinterpreting a paradigm_report built with a looser
threshold.

Genre-structural bias: on exam-format corpora (or anything else with a
closed set of structural formulas), run genre_stoplist.filter_genre_formulas
on the token list BEFORE computing either the paradigm-productivity report
or the keyness comparison that get passed in here. Confirmed empirically on
PES-2018-2022 that unfiltered exam-instruction language (above all
"odpowiedź", G2=370.26) outranks every real domain term — see README.

Thresholds (frequency_threshold, entropy_threshold on RegisterPoint.quadrant)
are starting points, not calibrated constants. Calibrate them empirically
against a hand-labeled sample from your own corpus before trusting the
quadrant labels for anything downstream (e.g. training-data stratification).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from .domain_specificity import KeynessResult
from .paradigm_productivity import ParadigmProductivityReport

DEFAULT_FREQUENCY_THRESHOLD = 1.0  # log2 ratio; 1.0 = target rate >= 2x reference rate
DEFAULT_ENTROPY_THRESHOLD = 0.5  # normalized entropy; see module docstring


@dataclass
class RegisterPoint:
    lemma: str
    normalized_entropy: float
    rel_freq_target: float
    rel_freq_reference: float
    g2: float
    occurrences: int

    @property
    def frequency_axis(self) -> float:
        """log2(target relative frequency / reference relative frequency).
        Symmetric around 0, unlike a raw ratio — makes the threshold in
        quadrant() a simple comparison instead of a magic ratio value.
        +inf when the lemma is entirely absent from the reference (maximally
        marked); this is a legitimate value, not a bug to special-case away."""
        if self.rel_freq_reference == 0:
            return float("inf")
        if self.rel_freq_target == 0:
            return float("-inf")
        return math.log2(self.rel_freq_target / self.rel_freq_reference)

    def quadrant(
        self,
        frequency_threshold: float = DEFAULT_FREQUENCY_THRESHOLD,
        entropy_threshold: float = DEFAULT_ENTROPY_THRESHOLD,
    ) -> str:
        """Classify this lemma into a register quadrant. See module
        docstring for why these two axes (not either alone) are needed, and
        for why the threshold defaults are starting points, not calibrated
        constants."""
        marked = self.frequency_axis >= frequency_threshold
        productive = self.normalized_entropy >= entropy_threshold
        if not marked and not productive:
            return "potoczny"
        if marked and not productive:
            return "specjalistyczny"
        if marked and productive:
            return "wyzszy_jezykowo"
        # frequent relative to reference AND low-entropy is the expected
        # colloquial cell; frequent-and-productive lands here instead --
        # uncommon combination, worth a manual look rather than silently
        # forcing it into one of the three named registers.
        return "niejednoznaczny"


@dataclass
class RegisterAxisReport:
    points: list[RegisterPoint] = field(default_factory=list)

    def by_quadrant(
        self,
        frequency_threshold: float = DEFAULT_FREQUENCY_THRESHOLD,
        entropy_threshold: float = DEFAULT_ENTROPY_THRESHOLD,
    ) -> dict[str, list[RegisterPoint]]:
        out: dict[str, list[RegisterPoint]] = {}
        for p in self.points:
            q = p.quadrant(frequency_threshold, entropy_threshold)
            out.setdefault(q, []).append(p)
        return out

    def summary(
        self,
        frequency_threshold: float = DEFAULT_FREQUENCY_THRESHOLD,
        entropy_threshold: float = DEFAULT_ENTROPY_THRESHOLD,
    ) -> dict[str, int]:
        return {q: len(pts) for q, pts in self.by_quadrant(frequency_threshold, entropy_threshold).items()}

    def print_summary(
        self,
        frequency_threshold: float = DEFAULT_FREQUENCY_THRESHOLD,
        entropy_threshold: float = DEFAULT_ENTROPY_THRESHOLD,
        n_per_quadrant: int = 8,
    ) -> None:
        by_q = self.by_quadrant(frequency_threshold, entropy_threshold)
        print(f"\n== Register axis ({len(self.points)} lemmas) ==")
        for quadrant, pts in sorted(by_q.items(), key=lambda kv: -len(kv[1])):
            print(f"\n{quadrant} (n={len(pts)}):")
            for p in sorted(pts, key=lambda p: -p.g2)[:n_per_quadrant]:
                print(
                    f"  {p.lemma:20s}  entropy={p.normalized_entropy:.3f}  "
                    f"freq_axis={p.frequency_axis:+.2f}  g2={p.g2:8.2f}  n={p.occurrences}"
                )


def build_register_axis(
    paradigm_report: ParadigmProductivityReport,
    keyness_results: list[KeynessResult],
    min_occurrences: int = 3,
) -> RegisterAxisReport:
    """Join a paradigm-productivity report and a keyness comparison into a
    single per-lemma register axis.

    paradigm_report must have been built with
    ParadigmProductivity(min_occurrences=N) where N >= min_occurrences --
    raises ValueError otherwise, rather than silently joining mismatched
    populations (see module docstring, "Population-threshold note").

    keyness_results is filtered here to freq_target >= min_occurrences, so
    it's fine to pass the full DomainSpecificity(...).compare(...) output
    without pre-filtering it yourself.

    Lemmas present on only one side (eligible for paradigm productivity but
    not for keyness, or vice versa) are dropped, not zero-filled -- a
    missing measurement is not the same as a measured zero, and silently
    filling one in would misrepresent the join as more complete than it is.
    """
    if paradigm_report.min_occurrences < min_occurrences:
        raise ValueError(
            f"paradigm_report was built with min_occurrences="
            f"{paradigm_report.min_occurrences}, lower than the "
            f"min_occurrences={min_occurrences} requested here. Rebuild it "
            f"with ParadigmProductivity(min_occurrences={min_occurrences}) "
            f"first -- joining mismatched thresholds adds sampling noise "
            f"that looks like signal."
        )

    keyness_by_lemma = {
        r.lemma: r for r in keyness_results if r.freq_target >= min_occurrences
    }

    points = []
    for stats in paradigm_report.eligible():
        kr = keyness_by_lemma.get(stats.lemma)
        if kr is None:
            continue
        points.append(
            RegisterPoint(
                lemma=stats.lemma,
                normalized_entropy=stats.normalized_entropy,
                rel_freq_target=kr.rel_freq_target,
                rel_freq_reference=kr.rel_freq_reference,
                g2=kr.g2,
                occurrences=stats.occurrences,
            )
        )
    return RegisterAxisReport(points=points)
