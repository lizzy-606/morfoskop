"""
End-to-end demo: two short texts of similar length and similar POS
distribution, but different paradigm productivity — one inflects
vocabulary, the other loops on the same forms. Plus a quick keyness
example on two mini-corpora.
"""

from morfoskop import MorphPipeline, ParadigmProductivity, DomainSpecificity
from morfoskop.report import print_paradigm_summary, print_keyness_summary

TEXT_GENERATIVE = """
Pies biegał po ogrodzie. Psa zobaczyłem z okna. Psu rzuciłem piłkę.
Z psem poszliśmy na spacer. O psie myślę codziennie. Kota nie było widać,
kot spał na parapecie, kotu nalałem mleka, z kotem bawiliśmy się wieczorem.
"""

TEXT_LOOPED = """
Psa widziałem wczoraj. Psa nakarmiłem rano. Psa wyprowadziłem na spacer.
Psa umyłem w wannie. Psa zawiozłem do weterynarza. Psa sfotografowałem.
Kota widziałem wczoraj. Kota nakarmiłem rano. Kota wyprowadziłem na spacer.
"""

DOMAIN_SPEECH_THERAPY = """
Afazja ruchowa utrudnia pacjentowi budowanie wypowiedzi. Terapeuta stosuje
metodę AAC, żeby wspomóc komunikację. Dysfunkcja artykulacyjna wymaga
ćwiczeń oddechowych. Pacjent z afazją korzysta z komunikatora.
"""

GENERAL_CORPUS = """
Pies biegał po ogrodzie. Dziecko bawiło się piłką na podwórku.
Samochód stał zaparkowany przy domu. Słońce świeciło mocno tego dnia.
Kobieta niosła zakupy do domu. Chłopiec czytał książkę w parku.
"""


def main():
    pipeline = MorphPipeline()  # defaults to pl_core_news_lg
    analyzer = ParadigmProductivity(min_occurrences=1)

    print("#" * 70)
    print("PART 1: paradigm productivity — generative vs. looped text")
    print("#" * 70)

    for label, text in [("GENERATIVE", TEXT_GENERATIVE), ("LOOPED", TEXT_LOOPED)]:
        print(f"\n{'=' * 20} {label} {'=' * 20}")
        tokens = pipeline.tokens_from_text(text)
        report = analyzer.analyze(tokens, pos="NOUN")
        print_paradigm_summary(report)

    print("\n" + "#" * 70)
    print("PART 2: domain specificity — speech therapy vs. general corpus")
    print("#" * 70)

    target_tokens = pipeline.tokens_from_corpus([DOMAIN_SPEECH_THERAPY])
    reference_tokens = pipeline.tokens_from_corpus([GENERAL_CORPUS])

    spec = DomainSpecificity(min_freq_target=1)
    results = spec.compare(target_tokens, reference_tokens)
    print_keyness_summary(results, n=10)


if __name__ == "__main__":
    main()
