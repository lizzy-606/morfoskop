# morfoskop

Measures two things in Polish text: how flexibly a word is actually inflected, and which words are unusually characteristic of a given domain.

## The idea in one paragraph

Take the word "matka" (mother). If a text uses it ten times and every single time it's "matki" (genitive), that word is doing one job over and over. If a text uses "matka" across five different cases — "matka", "matce", "matkę", "matką", "matki" — the same lemma is doing five jobs. Same word, same frequency, completely different behavior. `morfoskop` measures the second thing. Most tools measure the first.

## How this differs from StyloMetrix

StyloMetrix (Okulska et al., 2023, NASK) counts **morphological feature frequency per token**: how many times `Case=Gen` shows up in the text, how many times `Aspect=Perf`, normalized by document length. That's a measure of **distributional typicality** — how closely a text matches the average form distribution of a reference corpus. It tells you nothing about whether a given lexeme is used *generatively*, i.e. whether the author is actually moving across the paradigm or just repeating one form.

`morfoskop` counts **per lemma, not per token**. For each lemma, it checks how many *distinct* paradigm cells were attested, and how evenly usage is spread across them (entropy). Two texts can have identical `Case=Gen` frequency under StyloMetrix and completely different paradigm productivity under `morfoskop`.

Second, unrelated difference: `morfoskop` reads grammatical annotation through one consistent system (`token.morph`, Universal Dependencies) end to end. StyloMetrix's Polish inflection module mixes two annotation systems within the same category — `token.morph` in most places, the older positional tagset via `token.tag_` elsewhere (see `IN_V_FUTS`, `IN_V_IMP`, `IN_V_COND` in their repo). That inconsistency is avoided here by design, not by accident.

This tool grew out of that comparison — it's a separate methodology built to ask a different question, not a StyloMetrix fork or extension.

## Modules

### 1. `paradigm_productivity`

For nouns and adjectives: which grammatical cases were attested per lemma, out of the 7-member Polish case set (Nom, Gen, Dat, Acc, Ins, Loc, Voc), plus Shannon entropy of how evenly usage is spread across those cases.

For verbs: same logic, over attested (aspect, tense, mood) combinations.

Grounded in the **Paradigm Cell Filling Problem** and the **Low Conditional Entropy Conjecture** (Ackerman & Malouf, 2013, *Language*), and in Baayen's (1992) morphological productivity measures. Entropy of form distribution as an indicator of paradigm health is standard in that literature — not invented for this tool.

**A note on the entropy numbers you'll see:** plain Shannon entropy computed from raw counts is biased *downward* when a lemma has few examples — the fewer tokens you have, the more "unproductive" a word looks, even when it isn't. This is a known statistical artifact, not a linguistic finding. Practical rule: always report the token count (N) next to every entropy value, and treat anything below N=30 per lemma as low-confidence rather than putting it in the same table as well-sampled lemmas. If you need something more rigorous than a threshold, the Chao-Shen coverage-adjusted estimator (Chao & Shen, 2003) corrects for probability mass sitting in paradigm cells that exist but weren't observed in the sample — worth implementing if you're publishing comparisons across lemmas with very different frequencies.

### 2. `domain_specificity`

Compares lemma frequency between a target corpus and a reference corpus — classic log-likelihood ratio / keyness (Dunning, 1993; Rayson & Garside, 2000). A word that's rare overall but frequent in the target corpus signals domain specificity. No terminology dictionary needed (dedicated Polish domain-term lists barely exist anyway). Any reference corpus works — plugs naturally into Bielikans/SpeakLeash as a general-Polish baseline.

**Reference corpus size matters more than the formula.** With a ~200-token toy reference, G2 stays below the conventional significance threshold (3.84) for nearly every lemma — the measure isn't wrong, there just isn't enough contrast to compute against. A ~55k-word reference (50 Wikipedia articles) against a 200-question exam-domain target produced 387 lemmas significant at G2 > 3.84, several in the hundreds. Undersized references don't fail loudly; they fail by returning numbers that look plausible and aren't.

**Exam-format and other structured-genre corpora inflate keyness with document-format noise, not domain signal.** Verified on `speakleash/PES-2018-2022` (`choroby_wewnetrzne`, medical specialization exam) against a Wikipedia reference: the single highest-G2 lemma in the raw comparison was `odpowiedź` ("answer", G2=370.26) — outranking every genuine medical term, including `zapalenie` (303.31) and `nerka` (203.53). The cause: exam-instruction phrasing ("wskaż prawidłową odpowiedź") and answer-option residue (`b`, `1,2,3`) are structurally frequent in the target and structurally absent from general-Polish reference text, which is exactly what keyness is built to flag — it just isn't domain vocabulary. See `genre_stoplist` below.

### 3. `genre_stoplist`

Filters exam-instruction language (`odpowiedź`, `wskaż`, `prawidłowy`, `prawdziwy`, ...) and answer-option residue (single letters A–E, 3+-digit enumerations like `2,3,5`) out of a token list before it reaches either measure above. Closed, enumerable set — built from `PES-2018-2022`, not claimed to generalize to other exam formats without extension. Deliberately does *not* flag 2-digit comma patterns (`3,5`): Polish uses comma as the decimal separator, so a 2-digit pattern is ambiguous with a real value (dosage, lab result) — false negatives here are cheaper than deleting real clinical numbers.

Applying it to the PES example above: `odpowiedź`, `wskaż`, `b`, `1,2,3` drop out entirely; the top-10 keyness list becomes `zapalenie`, `nerka`, `choroba`, `chory`, `stężenie`, `obecność`, `objaw`, `lek`, `zespół`, `leczyć` — all genuine domain terms.

```python
from morfoskop.genre_stoplist import filter_genre_formulas

tokens = pipeline.tokens_from_text(text)
tokens = filter_genre_formulas(tokens)  # before analyze() / compare()
```

### 4. `register_axis`

Composes the outputs of `paradigm_productivity` and `domain_specificity` — does not modify either. Crosses entropy (productivity) with keyness-derived relative-frequency (markedness) into a 2D space, because entropy alone conflates two registers that should stay separate:

|  | low entropy | high entropy |
|---|---|---|
| **not marked vs. reference** | `potoczny` | — |
| **marked vs. reference** | `specjalistyczny` | `wyzszy_jezykowo` |

Specialist terminology tends to surface in one or two canonical forms (low entropy) despite being domain-marked (high keyness) — the same low-entropy signature colloquial speech has, for an unrelated reason. Keyness is the axis that separates them; entropy alone can't.

`build_register_axis()` enforces a single `min_occurrences` across both inputs before joining — `paradigm_productivity` and `domain_specificity` have independently-set eligibility thresholds, and joining them unreconciled adds sampling noise indistinguishable from a real effect. Raises `ValueError` rather than silently joining mismatched populations. Lemmas eligible on only one side are dropped, not zero-filled.

```python
from morfoskop.paradigm_productivity import ParadigmProductivity
from morfoskop.domain_specificity import DomainSpecificity
from morfoskop.register_axis import build_register_axis

paradigm = ParadigmProductivity(min_occurrences=3).analyze(tokens, pos="NOUN")
keyness = DomainSpecificity(min_freq_target=3).compare(target_tokens, reference_tokens)
axis = build_register_axis(paradigm, keyness, min_occurrences=3)
axis.print_summary()
```

**Quadrant thresholds (`frequency_threshold=1.0`, `entropy_threshold=0.5`) are starting points, not calibrated constants.** Calibrate against a hand-labeled sample from your own corpus before trusting the labels downstream. Confirmed on real data that the default entropy threshold can split a single genuine register across two quadrants: on the filtered PES corpus, `nerka` (entropy 0.139) landed in `specjalistyczny` while `zapalenie` (entropy 0.850) landed in `wyzszy_jezykowo` — both unambiguously medical terms, differing only in how often they happen to get inflected across contexts in that corpus. Left visible, not tuned away.

## Scope

Operates on the layer after spaCy tokenization — word-level morphology. Subword/BPE tokenization is a separate line of work (see preprints 1–4) and stays out of this tool on purpose.

Output is descriptive: entropy values, coverage ratios, keyness scores, with N reported alongside. Deciding what counts as a "good" or "bad" score for your use case — including where register quadrant boundaries sit — is a separate step you make explicitly, not something the tool decides for you.

## Morphological backend

Defaults to `pl_core_news_lg` (spaCy). `pl_core_news_sm` has a weak lemmatizer — confirmed failures include merging "kota" (genitive of "kot") into a separate lemma, lemmatizing "macie" (locative of "mata") as "mieć", and failing to merge capitalized sentence-initial "Psa" with lemma "pies" (producing a spurious lemma with zero measured entropy). These are reproduced, not hypothetical. Use `lg` for real work; `pl_nask` (HerBERT-based, IPI PAN) if available — backend is swappable, see `pipeline.py`.

All example numbers in this README (`domain_specificity`, `genre_stoplist`, `register_axis` sections) were produced on `pl_core_news_sm` for iteration speed — illustrative, not a methodology-clean result. Re-run on `lg` before citing specific values.

## Installation

```bash
pip install -e .
python -m spacy download pl_core_news_lg
```

## Usage

```bash
morfoskop paradigm --input text.txt
morfoskop keyness --target domain/ --reference general/
```

Programmatic use: see `examples/demo.py`.

## Status

Working skeleton. Verb metrics (aspect/tense/mood combinations) are simplified relative to the full complexity of the Polish verbal system — to be extended after first tests on a real corpus.

Current version measures paradigm productivity via lemma + grammatical tag (spaCy's `token.morph`) — entropy over attested case/tense labels per lemma. A finer-grained metric is in development: segmentation into root, prefix, and inflectional ending, to measure productivity at the level of word structure itself rather than the grammatical label spaCy assigns to it.

`register_axis` quadrant thresholds are uncalibrated defaults (see above) — calibration against a hand-labeled register sample is the next concrete step, not a solved problem.
