# morfoskop

Measures two things in Polish text: how flexibly a word is actually inflected, and which words are unusually characteristic of a given domain.

## The idea in one paragraph

Take the word "matka" (mother). If a text uses it ten times and every single time it's "matki" (genitive), that word is doing one job over and over. If a text uses "matka" across five different cases — "matka", "matce", "matkę", "matką", "matki" — the same lemma is doing five jobs. Same word, same frequency, completely different behavior. `morfoskop` measures the second thing. Most tools measure the first.

## How this differs from StyloMetrix

StyloMetrix (Okulska et al., 2023, NASK) counts **morphological feature frequency per token**: how many times `Case=Gen` shows up in the text, how many times `Aspect=Perf`, normalized by document length. That's a measure of **distributional typicality** — how closely a text matches the average form distribution of a reference corpus. It tells you nothing about whether a given lexeme is used *generatively*, i.e. whether the author is actually moving across the paradigm or just repeating one form.

`morfoskop` counts **per lemma, not per token**. For each lemma, it checks how many *distinct* paradigm cells were attested, and how evenly usage is spread across them (entropy). Two texts can have identical `Case=Gen` frequency under StyloMetrix and completely different paradigm productivity under `morfoskop`.

Second, unrelated difference: `morfoskop` reads grammatical annotation through one consistent system (`token.morph`, Universal Dependencies) end to end. StyloMetrix's Polish inflection module mixes two annotation systems within the same category — `token.morph` in most places, the older positional tagset via `token.tag_` elsewhere (see `IN_V_FUTS`, `IN_V_IMP`, `IN_V_COND` in their repo). That inconsistency is avoided here by design, not by accident.

This tool grew out of that comparison — it's a separate methodology built to ask a different question, not a StyloMetrix fork or extension.

## Two modules

### 1. `paradigm_productivity`

For nouns and adjectives: which grammatical cases were attested per lemma, out of the 7-member Polish case set (Nom, Gen, Dat, Acc, Ins, Loc, Voc), plus Shannon entropy of how evenly usage is spread across those cases.

For verbs: same logic, over attested (aspect, tense, mood) combinations.

Grounded in the **Paradigm Cell Filling Problem** and the **Low Conditional Entropy Conjecture** (Ackerman & Malouf, 2013, *Language*), and in Baayen's (1992) morphological productivity measures. Entropy of form distribution as an indicator of paradigm health is standard in that literature — not invented for this tool.

**A note on the entropy numbers you'll see:** plain Shannon entropy computed from raw counts is biased *downward* when a lemma has few examples — the fewer tokens you have, the more "unproductive" a word looks, even when it isn't. This is a known statistical artifact, not a linguistic finding. Practical rule: always report the token count (N) next to every entropy value, and treat anything below N=30 per lemma as low-confidence rather than putting it in the same table as well-sampled lemmas. If you need something more rigorous than a threshold, the Chao-Shen coverage-adjusted estimator (Chao & Shen, 2003) corrects for probability mass sitting in paradigm cells that exist but weren't observed in the sample — worth implementing if you're publishing comparisons across lemmas with very different frequencies.

### 2. `domain_specificity`

Compares lemma frequency between a target corpus and a reference corpus — classic log-likelihood ratio / keyness (Dunning, 1993; Rayson & Garside, 2000). A word that's rare overall but frequent in the target corpus signals domain specificity. No terminology dictionary needed (dedicated Polish domain-term lists barely exist anyway). Any reference corpus works — plugs naturally into Bielikans/SpeakLeash as a general-Polish baseline.

## Scope

Operates on the layer after spaCy tokenization — word-level morphology. Subword/BPE tokenization is a separate line of work (see preprints 1–4) and stays out of this tool on purpose.

Output is descriptive: entropy values, coverage ratios, keyness scores, with N reported alongside. Deciding what counts as a "good" or "bad" score for your use case is a separate step you make explicitly, not something the tool decides for you.

## Morphological backend

Defaults to `pl_core_news_lg` (spaCy). `pl_core_news_sm` has a weak lemmatizer — confirmed failures include merging "kota" (genitive of "kot") into a separate lemma, lemmatizing "macie" (locative of "mata") as "mieć", and failing to merge capitalized sentence-initial "Psa" with lemma "pies" (producing a spurious lemma with zero measured entropy). These are reproduced, not hypothetical. Use `lg` for real work; `pl_nask` (HerBERT-based, IPI PAN) if available — backend is swappable, see `pipeline.py`.

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
