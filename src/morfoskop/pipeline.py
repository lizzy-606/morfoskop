"""
Morphological backend access layer (spaCy).

Purpose of this module: everything that knows about the specific model
(name, how it's loaded, eventually swapping to pl_nask instead of
pl_core_news_*) is contained here. The rest of the package operates on
simple structures (TokenInfo), not spaCy objects — so swapping the backend
does not require changes in paradigm_productivity.py or
domain_specificity.py.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Iterator

import spacy
from spacy.language import Language
from spacy.tokens import Doc


DEFAULT_MODEL = "pl_core_news_lg"

# POS tags for which computing an inflectional paradigm makes sense at all
# in Polish.
INFLECTED_POS = {"NOUN", "PROPN", "ADJ", "VERB", "AUX"}


@dataclass(frozen=True)
class TokenInfo:
    """Simplified token representation — independent of spaCy."""

    text: str
    lemma: str
    pos: str
    morph: dict[str, str] = field(default_factory=dict)

    def has(self, feature: str, value: str) -> bool:
        return self.morph.get(feature) == value

    def feature_values(self, feature: str) -> tuple[str, ...]:
        """Some morph features can have multiple comma-separated values
        (e.g. Aspect=Imp,Perf for biaspectual forms like "dać"). Returns a
        tuple."""
        raw = self.morph.get(feature)
        if not raw:
            return ()
        return tuple(raw.split(","))


class MorphPipeline:
    """Thin wrapper around spaCy. Loads the model once, exposes token
    iteration as TokenInfo instead of raw spaCy objects."""

    def __init__(self, model_name: str = DEFAULT_MODEL, nlp: Language | None = None):
        self.model_name = model_name
        self._nlp = nlp

    @property
    def nlp(self) -> Language:
        if self._nlp is None:
            self._nlp = spacy.load(self.model_name)
        return self._nlp

    def process(self, text: str) -> Doc:
        return self.nlp(text)

    def process_many(self, texts: Iterable[str], batch_size: int = 50) -> Iterator[Doc]:
        yield from self.nlp.pipe(texts, batch_size=batch_size)

    @staticmethod
    def extract_tokens(doc: Doc, pos_filter: set[str] | None = None) -> list[TokenInfo]:
        """Converts a spaCy Doc into a list of TokenInfo. By default only
        POS tags subject to inflection (see INFLECTED_POS) — the rest
        (punctuation, conjunctions, etc.) are irrelevant here."""
        pos_filter = pos_filter or INFLECTED_POS
        out = []
        for token in doc:
            if token.pos_ not in pos_filter:
                continue
            if token.is_space or token.is_punct:
                continue
            morph_dict = {
                key: val
                for key, val in (
                    part.split("=", 1) for part in str(token.morph).split("|") if part
                )
            }
            out.append(
                TokenInfo(
                    text=token.text,
                    lemma=token.lemma_.lower(),
                    pos=token.pos_,
                    morph=morph_dict,
                )
            )
        return out

    def tokens_from_text(self, text: str, pos_filter: set[str] | None = None) -> list[TokenInfo]:
        return self.extract_tokens(self.process(text), pos_filter=pos_filter)

    def tokens_from_corpus(
        self, texts: Iterable[str], pos_filter: set[str] | None = None
    ) -> list[TokenInfo]:
        tokens: list[TokenInfo] = []
        for doc in self.process_many(texts):
            tokens.extend(self.extract_tokens(doc, pos_filter=pos_filter))
        return tokens
