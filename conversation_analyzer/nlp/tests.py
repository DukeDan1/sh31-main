'''Tests for NLP module.'''
import json
from django.test import TestCase, TransactionTestCase
import numpy as np
from analyzer.io.common import PendingRecord
from analyzer.io.nlp import NLP_ANALYZER
from analyzer.models import NLPTask
from nlp import keyword_extract

class NLPAnalyzerTests(TransactionTestCase):
    '''Checks if the analyzer is performing correctly.'''

    def test_thread_execution(self):
        '''See if the background thread commits the record correctly.'''
        pending_record = PendingRecord(NLPTask.get_mock(), 'result')
        thread = NLP_ANALYZER.analyze_single_string('Sad Glasgow', pending_record)
        thread.join()
        self.assertEqual('Glasgow', json.loads(NLPTask.get_mock().result)['topics'][0][0])

    def test_useful_words(self):
        '''Checks that the useful words preprocessing is as expected.'''
        pending_record = PendingRecord(NLPTask.get_mock(), 'result')
        thread = NLP_ANALYZER.analyze_single_string(
            'sleep sleep   myself Glasgow!!', pending_record)
        thread.join()
        expected = {'sleep', 'glasgow'}
        result = json.loads(NLPTask.get_mock().result)['useful_words']
        self.assertEqual(len(expected), len(result))
        self.assertEqual(expected, set(result))

class KeywordExtractionTests(TestCase):
    '''Check if the extraction of keywords is roughly correct.'''

    def test_keyword_extraction(self):
        '''Uses a predefined list and threshold to test correctness.'''
        keyword_set = keyword_extract.extract_keyword('there is a drugs store', 8,
                                                  np.array(['drug', 'mlm']))
        expected = [('drugs', 'drug'), ('store', None)]
        for index, keyword in enumerate(keyword_set):
            self.assertEqual(expected[index][0], keyword.keyword)
            self.assertEqual(expected[index][1], keyword.association)
