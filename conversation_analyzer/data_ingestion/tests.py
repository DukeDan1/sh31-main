'''Tests for data ingestion module.'''
import os

from django.conf import settings
from django.test import TestCase
from django.contrib.auth.models import User
from analyzer.models import Document, SystemUser
from data_ingestion import file_handling

ROOT_DIR = os.path.join(settings.BASE_DIR, 'data_ingestion')

class FileSaveTests(TestCase):
    '''Check if the file saving functionality is correctly integrated.'''

    def test_file_save_successful(self):
        '''Main function for testing'''
        processor = file_handling.FileProcessor(f'{ROOT_DIR}/test/files/unformatted2.txt')
        file = processor.process()
        user = User.objects.get_or_create(username='testuser')[0]
        uploader = SystemUser.objects.get_or_create(user=user)[0]
        media_store_name = file.save(uploader)
        common_path = os.path.commonpath((media_store_name, settings.MEDIA_ROOT))
        self.assertEqual(len(common_path), len(settings.MEDIA_ROOT))
        document = Document.objects.get(file=media_store_name)
        self.assertEqual(document.display_name, 'unformatted2.txt.json')


class FileProcessTests(TestCase):
    '''
    Checks if the structured file processing is working,
    any functions requiring an API key are skipped.
    '''

    def test_structured_csv(self):
        '''Tests if structured CSV is processed correctly.'''
        processor = file_handling.FileProcessor(f'{ROOT_DIR}/test/files/test.csv')
        processor.process()
        self.assertEqual(len(processor.file.parsed_data), 8)
        self.assertEqual(processor.file.parsed_data[0]['name'], 'Alice')
        self.assertEqual(processor.file.parsed_data[1]['body'], 'How are you today?')
        self.assertEqual(processor.file.parsed_data[2]['date'], '2022-01-02')

    def test_structured_txt(self):
        '''Tests if structured TXT is processed correctly.'''
        processor = file_handling.FileProcessor(f'{ROOT_DIR}/test/files/test.txt')
        processor.process()
        self.assertEqual(len(processor.file.parsed_data), 3)
        self.assertEqual(processor.file.parsed_data[0]['name'], 'Danny')
        self.assertEqual(
            processor.file.parsed_data[1]['body'],
            "Hey Danny, I'm good. Just finished reading the latest Harry Potter book. 📚 You?"
        )
        self.assertEqual(processor.file.parsed_data[2]['time'], '19:05:00')

    def test_structured_docx(self):
        '''Tests if structured DOCX is processed correctly.'''
        processor = file_handling.FileProcessor(f'{ROOT_DIR}/test/files/test.docx')
        processor.process()
        self.assertEqual(len(processor.file.parsed_data), 3)
        self.assertEqual(processor.file.parsed_data[0]['name'], 'Danny')
        self.assertEqual(
            processor.file.parsed_data[1]['body'],
            "Hey Danny, I'm good. Just finished reading the latest Harry Potter book. 📚 You?"
        )
        self.assertEqual(processor.file.parsed_data[2]['time'], '19:05:00')

    def test_structured_json(self):
        '''Tests if structured JSON is processed correctly.'''
        processor = file_handling.FileProcessor(f'{ROOT_DIR}/test/files/test.json')
        processor.process()
        self.assertEqual(len(processor.file.parsed_data), 2)
        self.assertEqual(processor.file.parsed_data[0]['name'], 'Alice')
        self.assertEqual(processor.file.parsed_data[1]['body'], 'Hello world!')

    def test_structured_xml(self):
        '''Tests if structured XML is processed correctly.'''
        processor = file_handling.FileProcessor(f'{ROOT_DIR}/test/files/test.xml')
        processor.process()
        self.assertEqual(len(processor.file.parsed_data), 2)
        self.assertEqual(processor.file.parsed_data[0]['name'], 'Alice')
        self.assertEqual(processor.file.parsed_data[1]['body'], 'Hello world!')

    def test_structured_srt(self):
        '''Tests if structured SRT is processed correctly.'''
        processor = file_handling.FileProcessor(f'{ROOT_DIR}/test/files/test.srt')
        processor.process()
        self.assertEqual(len(processor.file.parsed_data), 2)
        self.assertEqual(processor.file.parsed_data[0]['number'], '1')
        self.assertEqual(processor.file.parsed_data[0]['time'], '00:00:01,000 --> 00:00:02,000')
        self.assertEqual(processor.file.parsed_data[1]['body'], 'Hello world!')

    def test_unsupported(self):
        '''Tests if unsupported file is rejected correctly.'''
        processor = file_handling.FileProcessor(f'{ROOT_DIR}/test/files/test.pdf')
        with self.assertRaises(Exception) as context:
            processor.process()
        self.assertTrue('Unsupported file type' in str(context.exception))
