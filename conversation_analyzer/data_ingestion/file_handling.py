'''This module contains classes for reading and parsing files of various types'''
import json
import os
import openai
from docx import Document
import xmltodict
from dotenv import load_dotenv
from analyzer.io import ingestion
from analyzer.io.common import generic_openai_request
load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

class File:
    '''Base class for all file types'''

    def __init__(self, filename):
        self.filename = filename
        self.data = []
        self.parsed_data = []

    def get_data(self):
        '''Returns the parsed data if it exists, otherwise returns the raw data'''
        if self.parsed_data:
            return self.parsed_data
        return []

    def __str__(self):
        if self.parsed_data:
            return str(self.parsed_data)
        return str(self.data)

    def save(self, uploading_user):
        '''Saves the file in the media store, returns its name in the media store.'''
        filename = os.path.basename(self.filename)
        file, record = ingestion.get_saves_write_handle(f'{filename}.json', uploading_user)
        media_store_name = file.name
        with file:
            file.write(json.dumps(self.get_data(), indent=4))
        record.confirm()
        return media_store_name


class UnstructuredTextBasedFile(File):
    '''Base class for unstructured text-based file types, e.g. TXT, DOCX'''
    def __init__(self, filename):
        super().__init__(filename)
        self.default_formatting = True

    def set_default_formatting(self, default_formatting):
        '''Sets whether the file is in the default formatting provided by SAS or not'''
        self.default_formatting = default_formatting

    def get_first_entry(self):
        '''Returns the first entry in the file'''
        if self.data:
            return self.data[0]
        return None

    def parse(self):
        '''Parses the data in the file'''
        if self.default_formatting:
        # Parse the data using the format provided by SAS
            try:
                self.parsed_data = []
                for line in self.data:
                    date_time, message = line.split(',', 1)
                    date, time = date_time.split('T')
                    name, body = message.split(':', 1)

                    self.parsed_data.append({
                        "date": date.strip(),
                        "time": time.strip(),
                        "name": name.strip(),
                        "body": body.strip()
                    })
            except ValueError:
                # If the data is not in the format provided by SAS, use the AI to parse the data
                self.__parse_using_ai()
        else:
            # Use the AI to parse the data
            self.__parse_using_ai()

    def __parse_using_ai(self):
        '''Parses the data using the AI'''
        self.parsed_data = []
        def openai_parse(parsed_data):
            openai_request_data = ingestion.get_openai_request_config()

            openai_request_data['messages'].append({
                'role': 'user',
                'content': '\n'.join(self.data)
            })

            response = openai.ChatCompletion.create(**openai_request_data)
            parsed_data = json.loads(
                response["choices"][0]["message"]["tool_calls"][0]["function"]["arguments"]
            )
            return parsed_data["conversation"]

        self.parsed_data = generic_openai_request(openai_parse, self.parsed_data)

class TXTFile(UnstructuredTextBasedFile):
    '''Class for reading and parsing TXT files'''

    def read(self):
        '''Reads the data from the file'''
        with open(self.filename, 'r', encoding="utf-8") as f:
            self.data = f.read().split('\n')


class CSVFile(File):
    '''Class for reading and parsing CSV files'''

    def read(self):
        '''Reads the data from the file'''
        with open(self.filename, 'r', encoding="utf-8") as f:
            self.data = f.read().split('\n')

    def parse(self):
        '''Parses the data in the file'''
        column_names = self.data[0].split(',')
        self.data = self.data[1:]
        self.parsed_data = []
        for row in self.data:
            self.parsed_data.append(dict(zip(column_names, row.split(','))))

class SRTFile(File):
    '''Class for reading and parsing SRT files'''

    def read(self):
        '''Reads the data from the file'''
        with open(self.filename, 'r', encoding="utf-8") as f:
            self.data = f.read().split('\n\n')

    def parse(self):
        '''Parses the data in the file'''
        self.parsed_data = []
        for row in self.data:
            row = row.split('\n')
            self.parsed_data.append({
                "number": row[0],
                "time": row[1],
                "body": row[2]
            })

class JSONFile(File):
    '''Class for reading and parsing JSON files'''

    def read(self):
        '''Reads the data from the file'''
        with open(self.filename, 'r', encoding="utf-8") as f:
            self.data = f.read()

    def parse(self):
        '''Parses the data in the file'''
        self.parsed_data = json.loads(self.data)




class XMLFile(File):
    '''Class for reading and parsing XML files'''

    def read(self):
        '''Reads the data from the file'''
        with open(self.filename, 'r', encoding="utf-8") as f:
            self.data = f.read()

    def parse(self):
        '''Parses the data in the file'''
        def find_list(d):
            for v in d.values():
                if isinstance(v, list):
                    return v
                if isinstance(v, dict):
                    return find_list(v)
            return None

        self.parsed_data = find_list(xmltodict.parse(self.data))


class DOCXFile(UnstructuredTextBasedFile):
    '''Class for reading and parsing DOCX files'''

    def read(self):
        '''Reads the data from the file'''
        doc = Document(self.filename)
        full_text = []
        for para in doc.paragraphs:
            full_text.append(para.text)
        self.data = full_text

class InvalidFileException(Exception):
    '''Exception for invalid file types'''

class FileProcessor:
    '''Class for processing files of various types'''
    def __init__(self, filename):
        self.filename = filename
        self.file = None

    def process(self):
        '''Processes the file and returns the file object'''
        self.file = self.get_file_object(self.filename)
        self.file.read()
        self.file.parse()
        return self.file

    def is_valid(self):
        """Checks if file has been parsed."""
        if self.file.get_data():
            return True
        return False

    def get_file_object(self, filename):
        '''Factory for creating File objects'''
        self.filename = f"{filename}"
        _, ext = os.path.splitext(self.filename)

        if ext == '.csv':
            return CSVFile(self.filename)
        if ext == '.txt':
            return TXTFile(self.filename)
        if ext == '.docx':
            return DOCXFile(self.filename)
        if ext == '.json':
            return JSONFile(self.filename)
        if ext == '.xml':
            return XMLFile(self.filename)
        if ext == '.srt':
            return SRTFile(self.filename)
        raise InvalidFileException('Unsupported file type')
