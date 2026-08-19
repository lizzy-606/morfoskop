# morfoskop

A tool for measuring **inflectional paradigm productivity** and **domain
specificity** in Polish text — built as a deliberate alternative to the
StyloMetrix approach (Okulska et al., 2023, NASK), not a clone of it.

## How this differs from StyloMetrix

StyloMetrix counts **morphological feature frequency per token**: how many
times `Case=Gen` occurred in the text, how many times `Aspect=Perf`,
normalized by document length. That is a measure of **distributional
typicality** — it tells you how closely a text matches the average form
distribution in a reference corpus. It says nothing about whether a lexeme
is used *generatively* — whether the author actually moves across the
paradigm, or just repeats the same form over and over.

`morfoskop` counts differently: **per lemma, not per token**. For each
lemma it checks how many *distinct* paradigm cells were attested in the
text, and how evenly usage is distributed across them (entropy). Two texts
can have identical `Case=Gen` frequency under StyloMetrix and completely
different paradigm productivity under `morfoskop` — one might inflect the
same noun across five cases, the other might repeat the genitive of one
different word ten times.

Second difference: `morfoskop` does not mix two annotation systems within
one category. StyloMetrix's Polish inflection module sometimes reads
`token.morph` and sometimes falls back to the old positional tagset via
`token.tag_` (see `IN_V_FUTS`, `IN_V_IMP`, `IN_V_COND` in their repo). Here
everything goes through `token.morph` (Universal Dependencies), consistently.

## Two modules

### 1. `paradigm_productivity` — paradigm productivity

For nouns and adjectives: the set of attested cases per lemma, Shannon
entropy of the case-usage distribution, coverage ratio against the
7-member set of Polish cases (Nom, Gen, Dat, Acc, Ins, Loc, Voc).

For verbs: the set of attested (aspect, tense, mood) combinations per
lemma, same entropy logic.

Theoretical grounding: this is not an ad hoc invention — it draws on the
**Paradigm Cell Filling Problem** and the **Low Conditional Entropy
Conjecture** (Ackerman & Malouf, 2013, *Language*), and on Baayen's (1992)
morphological productivity measures (type/token ratio as an estimator of
productivity). Entropy of form distribution as an indicator of paradigm
"health" is a standard tool in that literature, not an original shortcut.

### 2. `domain_specificity` — domain specificity (specialist vocabulary)

Does not require a terminology dictionary (which barely exists for Polish
specialist domains anyway — already documented in the NSM/frequency-resource
notes). Instead: comparison of lemma frequency between a target corpus and
a reference corpus, classic **log-likelihood ratio / keyness** (Dunning,
1993; Rayson & Garside, 2000). A word that is rare overall but frequent in
the domain corpus signals specificity — no pre-existing term list required.
Works with any reference corpus — naturally plugs into Bielikans/SpeakLeash
as a general-Polish reference.

## What this tool does NOT do

- It does not tokenize at the subword/BPE level. It operates on the layer
  after spaCy tokenization — the entire BPE/tokenizer layer stays a separate
  thread (preprints 1–4), deliberately unconnected here.
- It does not reproduce or expose the doctoral sequential method. The
  measures here are general, published morphological literature — not
  unpublished know-how.
- It is not a ready-made "quality" classifier for text. It returns
  descriptive numbers; interpreting quality thresholds is a separate,
  deliberate decision, not something quietly baked in the way it is in
  the Bielik quality classifier.

## Morphological backend

Defaults to `pl_core_news_lg` (spaCy). **Note**: `pl_core_news_sm` has a
weak lemmatizer — in testing it confused "kota" (genitive singular of
"kot") with a separate lemma "kota", and lemmatized "macie" (locative
singular of "mata") as "mieć". A live end-to-end run on `sm` also failed
to merge capitalized sentence-initial "Psa" with the lemma "pies",
producing a spurious separate lemma with zero measured entropy — this is
a confirmed, reproduced failure mode, not a hypothetical one. Use `lg` for
research work; ideally `pl_nask` (HerBERT-based, IPI PAN) if available —
the backend is swappable, see `pipeline.py`.

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

or programmatically — see `examples/demo.py`.

## Status

Working skeleton. Verb metrics (aspect/tense/mood combinations) are
simplified relative to the full complexity of the Polish verbal system —
to be extended after first tests on a real corpus.
