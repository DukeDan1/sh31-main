'''This file is to get the predictions of the nlp'''
import json
from multiprocessing.dummy import Pool
from pathlib import Path
from os import path
import string
import threading
import demoji
from django.conf import settings
import flair
from flair.data import Sentence
from flair.nn import Classifier
from flair.models import TextRegressor
import numpy as np
import spacy

flair.cache_root = Path(path.join(settings.BASE_DIR, 'nlp/.flair'))

class NLPAnalyzer:
    '''Wrapper to manage models and analysis.'''

    def __init__(self):
        '''Loads models for analysis.'''
        self.pool = Pool(4)
        self.units = {}
        self.units['ner'] = Classifier.load(path.join(settings.BASE_DIR,
            'nlp/.flair/models/ner-english-ontonotes-large/' +
            'models--flair--ner-english-ontonotes-large/blobs/' +
            '93ccd06d32bae9fde24d34cd86d81d0aa687c42dd531a0e7cf4b8d81c6eefc71'))
        self.units['sentiment'] = Classifier.load('sentiment')
        for emotion in ('sad', 'fear', 'anger', 'joy'):
            self.units[emotion] = TextRegressor.load(path.join(settings.BASE_DIR.parent,
                f'resources/taggers/wassa/{emotion}/final-model.pt'))
        self.units['sm'] = spacy.load("en_core_web_sm")

    def analyze_pooled(self, sentences, pending_records):
        '''Runs analysis on strings using a pool.'''
        self.pool.starmap(self.unthreaded_prediction, zip(sentences, pending_records))
        return self.pool

    def analyze_single_string(self, sentence, pending_record):
        '''Runs analysis on the given string using a thread.'''
        thread = threading.Thread(target=self.unthreaded_prediction,
                                  args=[sentence, pending_record])
        thread.daemon = True
        thread.start()
        return thread

    def unthreaded_prediction(self, sentence, pending_record):
        '''Run prediction on a single string without fancy trading.'''
        results = {}
        for emotion in ('sad', 'fear', 'anger', 'joy'):
            results[f'{emotion}_extreme'] = float(
                self._run_prediction(emotion, sentence)[0].data_point.tag)
        sentiment_label = self._run_prediction('sentiment', sentence)[0]
        results['sentiment'] = sentiment_label.score
        if sentiment_label.value == 'NEGATIVE':
            results['sentiment'] *= -1

        topics = self._run_prediction('ner', sentence)
        results['topics'] = [(topic.data_point.text, topic.value) for topic in topics]
        results['useful_words'] = self._extract_sentence_useful_words(sentence)

        results['risk'] = self._calculate_risk(results)

        pending_record.confirm(json.dumps(results))

    def _run_prediction(self, unit_name, in_sentence):
        '''Common routines for all models.'''
        sentence = Sentence(in_sentence)
        self.units[unit_name].predict(sentence)
        return sentence.get_labels()

    def _extract_sentence_useful_words(self, sentence):
        '''Filters the string into words which are useful.'''
        useful_words = set()
        for word in sentence.split():
            word = demoji.replace(word, '')
            word = word.rstrip(string.punctuation)
            word = word.lower()
            if len(word) != 0 and not self.units['sm'](word)[0].is_stop:
                useful_words.add(word)
        return list(useful_words)

    def _calculate_risk(self, results):
        '''Calculates primitive risk score from sentiment and emotions.'''
        def rescaler(in_data):
            return np.tanh(in_data)
        risk = -results["fear_extreme"]-results["sad_extreme"]-results[
            "anger_extreme"] + results["joy_extreme"]
        risk = rescaler(rescaler(risk) + results["sentiment"])
        return risk
