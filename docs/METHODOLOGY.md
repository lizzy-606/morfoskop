Methodology
Known limitation, empirically verified (not hypothetical)

Running examples/demo.py on pl_core_news_sm revealed a lemmatization error identical in kind to the one found on first contact with the StyloMetrix repo ("Kota" → lemma "kota" instead of "kot"): in the GENERATIVE text, the capitalized sentence-initial form "Psa" was not merged with the lemma "pies" — a separate, spurious lemma "psa" was created with distinct_cells=1. This deflates the measured productivity for "pies" and is a hard argument against using sm for research work. To verify: whether pl_core_news_lg has the same problem, or only the small variant. Recommended next step: rerun the demo on lg and, eventually, on pl_nask.

Why entropy, not just cell count

Cell count alone (distinct_cells) would conflate a lemma used twice in two different cases (apparently full "productivity") with a lemma used 50 times across 5 cases unevenly (e.g. 40× genitive, 2–3× the rest). Shannon entropy of the usage distribution distinguishes these cases: it penalizes unevenness, not just lack of variety in general. This follows standard practice in the literature on inflectional paradigm entropy.

Why raw entropy needs a caveat

The Shannon entropy estimator used here is the plug-in (maximum-likelihood) estimator — it is known to be downward biased for small samples, and the bias grows as the number of tokens per lemma shrinks relative to the number of possible paradigm cells. The min_occurrences threshold below mitigates this at the corpus-average level, but does not correct the entropy value itself for a given lemma. Chao & Shen's (2003) coverage-adjusted estimator addresses this directly and is a planned improvement.

Why the min_occurrences threshold

A lemma used once necessarily has distinct_cells=1 and entropy 0 — not because it is "non-generative," but because it never had the chance to show otherwise. Statistics below the occurrence threshold are excluded from corpus-level averages (eligible()), to avoid artificially deflating the mean with rare, single-occurrence items. This is the same problem as interpreting the finding in Preprint IV (a result based on 1 item / 2 models) — a small sample per unit of analysis gives an unstable result, and the same rigor applies here.

Bibliography

Ackerman, F., & Malouf, R. (2013). Morphological organization: The low conditional entropy conjecture. Language, 89(3), 429–464. https://doi.org/10.1353/lan.2013.0054

Baayen, R. H. (1992). Quantitative aspects of morphological productivity. In G. Booij & J. van Marle (Eds.), Yearbook of morphology 1991 (pp. 109–149). Kluwer Academic Publishers.

Chao, A., & Shen, T. J. (2003). Nonparametric estimation of Shannon's index of diversity when there are unseen species in sample. Environmental and Ecological Statistics, 10(4), 429–443. https://doi.org/10.1023/A:1026096204727

Dunning, T. (1993). Accurate methods for the statistics of surprise and coincidence. Computational Linguistics, 19(1), 61–74.

Okulska, I., Stetsenko, D., Kołos, A., Karlińska, A., Głąbińska, K., & Nowakowski, A. (2023). StyloMetrix: An open-source multilingual tool for representing stylometric vectors [Preprint]. arXiv. https://arxiv.org/abs/2309.12810

Rayson, P., & Garside, R. (2000). Comparing corpora using frequency profiling. In The Workshop on Comparing Corpora (pp. 1–6). Association for Computational Linguistics. https://doi.org/10.3115/1117729.1117730

Tuora, R., & Kobyliński, Ł. (2019). Integrating Polish language tools and resources in spaCy. In Proceedings of PP-RAI 2019 Conference (pp. 210–214). Department of Systems and Computer Networks, Faculty of Electronics, Wrocław University of Science and Technology.
