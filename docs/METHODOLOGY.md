# Methodology

## Known limitation, empirically verified (not hypothetical)

Running `examples/demo.py` on `pl_core_news_sm` revealed a lemmatization
error identical in kind to the one found on first contact with the
StyloMetrix repo ("Kota" → lemma "kota" instead of "kot"): in the
GENERATIVE text, the capitalized sentence-initial form "Psa" was not
merged with the lemma "pies" — a separate, spurious lemma "psa" was
created with `distinct_cells=1`. This deflates the measured productivity
for "pies" and is a hard argument against using `sm` for research work.
To verify: whether `pl_core_news_lg` has the same problem, or only the
small variant. Recommended next step: rerun the demo on `lg` and,
eventually, on `pl_nask`.

## Why entropy, not just cell count

Cell count alone (`distinct_cells`) would conflate a lemma used twice in
two different cases (apparently full "productivity") with a lemma used 50
times across 5 cases unevenly (e.g. 40× genitive, 2–3× the rest). Shannon
entropy of the usage distribution distinguishes these cases: it penalizes
unevenness, not just lack of variety in general. This follows standard
practice in the literature on inflectional paradigm entropy.

## Why the `min_occurrences` threshold

A lemma used once necessarily has `distinct_cells=1` and entropy 0 — not
because it is "non-generative", but because it never had the chance to
show otherwise. Statistics below the occurrence threshold are excluded
from corpus-level averages (`eligible()`), to avoid artificially deflating
the mean with rare, single-occurrence items. This is the same problem as
interpreting the finding in Preprint IV (a result based on 1 item / 2
models) — a small sample per unit of analysis gives an unstable result,
and the same rigor applies here.

## Bibliography (APA 7)

Ackerman, F., & Malouf, R. (2013). Morphological organization: The low
conditional entropy conjecture. *Language, 89*(3), 429–464.

Baayen, R. H. (1992). Quantitative aspects of morphological productivity.
In G. Booij & J. van Marle (Eds.), *Yearbook of Morphology 1991* (pp.
109–149). Kluwer Academic Publishers.

Dunning, T. (1993). Accurate methods for the statistics of surprise and
coincidence. *Computational Linguistics, 19*(1), 61–74.

Okulska, I., Stetsenko, D., Kołos, A., Karlińska, A., Głąbińska, K., &
Nowakowski, A. (2023). *StyloMetrix: An open-source multilingual tool for
representing stylometric vectors* (arXiv:2309.12810). arXiv.
https://arxiv.org/abs/2309.12810

Rayson, P., & Garside, R. (2000). Comparing corpora using frequency
profiling. In *Proceedings of the Workshop on Comparing Corpora* (pp.
1–6). Association for Computational Linguistics.

Tuora, R., & Kobyliński, Ł. (2019). Integrating Polish language tools and
resources in spaCy. In *Proceedings of PP-RAI'2019* (pp. 41–50). Wrocław,
Poland.
