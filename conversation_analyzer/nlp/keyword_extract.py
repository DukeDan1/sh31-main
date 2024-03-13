'''Utilities for keyword extraction and identification.'''
from typing import Generator
from collections import namedtuple

import numpy as np
import numpy.typing as npt
import pandas as pd
import spacy

from conversation_analyzer.settings import BASE_DIR

_tokenize = spacy.load('en_core_web_sm')
_word_vectors = np.load(f'{BASE_DIR}/nlp/glove_vecs.npz')
_word_vecs, _words = _word_vectors['word_vecs'], _word_vectors['words']

Keyword = namedtuple('Keyword', ['keyword', 'association', 'score'])

_association_df = pd.read_csv(f'{BASE_DIR}/nlp/risk_association.csv')

association = _association_df['association'].to_numpy()
score = _association_df['score'].to_numpy()


class KeywordSet:
    '''Set to iterate over all found keywords.'''

    def __init__(
        self, keywords: npt.NDArray[np.str_],
        associations: npt.NDArray[np.str_],
        scores: npt.NDArray[np.float64],
        ):
        self._keywords = keywords
        self._associations = associations
        self._scores = scores

    def keywords(self) -> Generator[Keyword, None, None]:
        '''Gets a generator for all keywords in the set, sorted in order.'''
        for index in np.argsort(self._scores):
            yield Keyword(self._keywords[index], self._associations[index], self._scores[index])

    def __iter__(self) -> Generator[Keyword, None, None]:
        return self.keywords()


def extract_keyword(
    message: str,
    cutoff: float,
    associations: npt.NDArray[np.str_],
    ) -> KeywordSet:
    '''Extracts a keyword set from a message, all keywords above a cutoff is assigned 'other'.'''
    tokens = _tokenize(message)
    keywords = np.array([token.text for token in tokens if token.pos_ in ('PROPN', 'NOUN')])
    association_vecs = _word_vecs[_words.searchsorted(associations)]

    keyword_search = _words.searchsorted(keywords)
    keyword_search = keyword_search[_words[keyword_search % len(_words)] == keywords]
    keyword_vecs = _word_vecs[keyword_search]
    keyword_scores = np.linalg.norm(keyword_vecs[:, None, :]
        .repeat(len(association_vecs), axis=1) - association_vecs, axis=-1)

    selected_assocs = associations[np.argmin(keyword_scores, axis=1)]
    selected_scores = np.min(keyword_scores, axis=1)
    def cutoff_replace(array, default):
        return np.where(selected_scores < cutoff, array, default)

    return KeywordSet(_words[keyword_search],
                      cutoff_replace(selected_assocs, None),
                      cutoff_replace(selected_scores, np.inf))
