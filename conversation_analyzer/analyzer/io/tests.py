'''Tests for IO modules.'''

from django.test import TestCase
from analyzer.io.common import AsyncPendingRecord, PendingRecord
from analyzer.models import Document, Profile

class AsyncPendingRecordTests(TestCase):
    '''Tests for AsyncPendingRecord.'''

    def test_lockless_async(self):
        '''Tests that it does not lock tables in the database.'''
        Profile.objects.create(name='Anonymous')
        def fulfill(model, value):
            model.note = value
            return model
        def selector():
            return Profile.objects.get(name='Anonymous')
        pending_record = AsyncPendingRecord(fulfill, selector)
        # will fail if this is not lockless.
        Profile.objects.create(name='John')
        pending_record.confirm('What?')
        self.assertEqual('What?', Profile.objects.get(name='Anonymous').note)

class PendingRecordTests(TestCase):
    '''Tests for PendingRecord.'''

    def test_confirm(self):
        '''Tests that the confirm mechanism is working.'''
        model = Profile.objects.create(name='Anonymous')
        pending_record = PendingRecord(model, 'note')
        pending_record.confirm('What?')
        self.assertEqual('What?', Profile.objects.get(name='Anonymous').note)

    def test_accept(self):
        '''Tests that documents are accepted correctly.'''
        pending_record = PendingRecord(Document.get_mock())
        pending_record.accept()
        document = Document.objects.get(pk=1)
        self.assertTrue(document.accepted)
        self.assertTrue(document.is_ingestion_output)
