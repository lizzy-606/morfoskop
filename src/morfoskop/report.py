from __future__ import annotations

import csv
from pathlib import Path

from .domain_specificity import KeynessResult
from .paradigm_productivity import ParadigmProductivityReport


def paradigm_report_to_csv(report: ParadigmProductivityReport, path: str | Path) -> None:
    path = Path(path)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            ["lemma", "pos", "occurrences", "distinct_cells", "coverage", "normalized_entropy"]
        )
        for stats in sorted(
            report.lemma_stats.values(), key=lambda s: s.occurrences, reverse=True
        ):
            writer.writerow(
                [
                    stats.lemma,
                    stats.pos,
                    stats.occurrences,
                    stats.distinct_cells,
                    f"{stats.coverage:.3f}" if stats.coverage is not None else "",
                    f"{stats.normalized_entropy:.3f}",
                ]
            )


def keyness_to_csv(results: list[KeynessResult], path: str | Path) -> None:
    path = Path(path)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            ["lemma", "freq_target", "freq_reference", "g2", "direction", "significant"]
        )
        for r in results:
            writer.writerow(
                [r.lemma, r.freq_target, r.freq_reference, f"{r.g2:.2f}", r.direction, r.significant()]
            )


def print_paradigm_summary(report: ParadigmProductivityReport) -> None:
    print(f"\n== Paradigm: {report.pos} ==")
    print(f"Lemmas (>= {report.min_occurrences} occurrences): {len(report.eligible())}")
    cov = report.mean_coverage()
    ent = report.mean_normalized_entropy()
    if cov is not None:
        print(f"Mean paradigm coverage: {cov:.2%}")
    if ent is not None:
        print(f"Mean normalized entropy: {ent:.3f}")

    print("\nMost productive (form variety):")
    for s in report.top_productive(5):
        print(f"  {s.lemma:20s}  cells={s.distinct_cells:2d}  entropy={s.normalized_entropy:.3f}  n={s.occurrences}")

    print("\nMost repetitive (many occurrences, same form):")
    for s in report.top_repetitive(5):
        print(f"  {s.lemma:20s}  cells={s.distinct_cells:2d}  entropy={s.normalized_entropy:.3f}  n={s.occurrences}")


def print_keyness_summary(results: list[KeynessResult], n: int = 15) -> None:
    print(f"\n== Domain-specific vocabulary (top {n}) ==")
    shown = [r for r in results if r.direction == "target"][:n]
    for r in shown:
        print(
            f"  {r.lemma:20s}  G2={r.g2:8.2f}  target={r.freq_target:4d}  ref={r.freq_reference:4d}"
        )
