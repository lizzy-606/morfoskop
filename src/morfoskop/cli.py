from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .pipeline import MorphPipeline, DEFAULT_MODEL
from .paradigm_productivity import ParadigmProductivity
from .domain_specificity import DomainSpecificity
from .report import (
    print_paradigm_summary,
    print_keyness_summary,
    paradigm_report_to_csv,
    keyness_to_csv,
)


def _read_texts(path: Path) -> list[str]:
    if path.is_dir():
        return [p.read_text(encoding="utf-8") for p in sorted(path.glob("*.txt"))]
    return [path.read_text(encoding="utf-8")]


def cmd_paradigm(args: argparse.Namespace) -> None:
    pipeline = MorphPipeline(model_name=args.model)
    texts = _read_texts(Path(args.input))
    tokens = pipeline.tokens_from_corpus(texts)

    analyzer = ParadigmProductivity(min_occurrences=args.min_occurrences)
    reports = analyzer.analyze_all(tokens, pos_list=("NOUN", "ADJ", "VERB"))

    for pos, report in reports.items():
        print_paradigm_summary(report)
        if args.csv_out:
            out_path = Path(args.csv_out) / f"paradigm_{pos.lower()}.csv"
            out_path.parent.mkdir(parents=True, exist_ok=True)
            paradigm_report_to_csv(report, out_path)
            print(f"  -> saved: {out_path}")


def cmd_keyness(args: argparse.Namespace) -> None:
    pipeline = MorphPipeline(model_name=args.model)
    target_texts = _read_texts(Path(args.target))
    reference_texts = _read_texts(Path(args.reference))

    target_tokens = pipeline.tokens_from_corpus(target_texts)
    reference_tokens = pipeline.tokens_from_corpus(reference_texts)

    analyzer = DomainSpecificity(min_freq_target=args.min_freq)
    results = analyzer.compare(target_tokens, reference_tokens)

    print_keyness_summary(results, n=args.top)
    if args.csv_out:
        out_path = Path(args.csv_out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        keyness_to_csv(results, out_path)
        print(f"\n-> saved: {out_path}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="morfoskop")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="spaCy model (default: %(default)s)")
    sub = parser.add_subparsers(dest="command", required=True)

    p_paradigm = sub.add_parser("paradigm", help="Inflectional paradigm productivity")
    p_paradigm.add_argument("--input", required=True, help="A .txt file or a directory of .txt files")
    p_paradigm.add_argument("--min-occurrences", type=int, default=2, dest="min_occurrences")
    p_paradigm.add_argument("--csv-out", default=None, help="Directory for output CSV files")
    p_paradigm.set_defaults(func=cmd_paradigm)

    p_key = sub.add_parser("keyness", help="Domain specificity (target vs reference)")
    p_key.add_argument("--target", required=True, help="File or directory — domain corpus")
    p_key.add_argument("--reference", required=True, help="File or directory — reference corpus")
    p_key.add_argument("--min-freq", type=int, default=3, dest="min_freq")
    p_key.add_argument("--top", type=int, default=20)
    p_key.add_argument("--csv-out", default=None, help="Output CSV file")
    p_key.set_defaults(func=cmd_keyness)

    args = parser.parse_args(argv)
    args.func(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
