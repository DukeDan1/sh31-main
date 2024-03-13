'''Utility functions for I/O operations.'''
import json
import os
from typing import Any, Callable, Generic, TypeVar
from django.conf import settings
from django.db import models
from analyzer.models import Document
import openai



T = TypeVar('T', bound=models.Model)

class AsyncPendingRecord():
    '''Asynchronous record to be confirmed.'''

    def __init__(self, fulfill: Callable[[T, Any], T], selector: Callable[[], T]):
        '''Initializes the pending record.'''
        self.fulfill = fulfill
        self.selector = selector

    def confirm(self, fulfill_value: Any):
        '''Confirms that the record should be committed.'''
        model = self.selector()
        if model is not None:
            model = self.fulfill(model, fulfill_value)
            model.save()

class PendingRecord(Generic[T]):
    '''Record to be confirmed by the consumer.'''

    def __init__(self, model: T, fulfill_attr: str|None = None):
        """Initializes the pending record."""
        self.model = model
        self.fulfill_attr = fulfill_attr

    def confirm(self, fulfill_value: Any = None):
        '''Confirms that the record should be committed.'''
        if self.fulfill_attr is not None:
            setattr(self.model, self.fulfill_attr, fulfill_value)
        self.model.save()

    def accept(self):
        """Accepts the record, and marks it as accepted."""
        self.model.accepted = True
        self.model.is_ingestion_output = True
        self.model.save()

    def get_openai_data(self, parsed_file):
        """Returns the OpenAI data for the record."""
        response_object = {}

        def request_data(response_object, parsed_file):
            with open(
                os.path.join(settings.STATIC_DIR, 'openAIRequestAnalysis.json'),
                'r',
                encoding='utf8'
            ) as f:
                file_data = json.loads(f.read())  # Load file contents as a string
                for key in ('analyser', 'contradictions', 'locations', 'behaviour'):
                    request = file_data[key]
                    request['messages'].append({
                        'role': 'user',
                        'content': json.dumps(parsed_file)
                    })
                    print("[LOG] Making OpenAI request...")
                    response = openai.ChatCompletion.create(**request)
                    response_object.update(
                        json.loads(
                            response
                            ["choices"][0]["message"]["tool_calls"][0]["function"]["arguments"]
                        )
                    )

            return response_object

        self.model.openai_data = generic_openai_request(request_data, response_object, parsed_file)
        self.model.save()

    def reject(self):
        """Rejects the record, and deletes it from the database."""
        path_original = os.path.join(settings.MEDIA_ROOT, str(self.model.file))
        path_parsed = os.path.join(settings.MEDIA_ROOT, 'ingestion_saves', str(self.model.uuid))
        uuid, ext = os.path.splitext(str(self.model.file).rsplit('/', maxsplit=1)[-1])
        path_parsed += ext
        os.unlink(path_original)
        os.unlink(path_parsed)
        self.model.delete()
        Document.objects.filter(file__contains=uuid).delete()

def write_unhandled_error(error, caller: str):
    """Writes an unhandled error to a file."""
    with open('unhandled_errors.txt', 'a', encoding='utf8') as file:
        file.write("Error in " + caller + ": " + str(error) + "\n")
        file.close()

def generic_openai_request(api_call, *args):
    """Makes a generic OpenAI request."""
    retry = True
    try:
        return api_call(*args)
    except openai.error.Timeout as e:
        #Handle timeout error, e.g. retry or log
        print(f"OpenAI API request timed out: {e}")
    except openai.error.APIError as e:
        #Handle API error, e.g. retry or log
        print(f"OpenAI API returned an API Error: {e}")
    except openai.error.APIConnectionError as e:
        #Handle connection error, e.g. check network or log
        print(f"OpenAI API request failed to connect: {e}")
    except openai.error.InvalidRequestError as e:
        #Handle invalid request error, e.g. validate parameters or log
        retry = False
        print(f"OpenAI API request was invalid: {e}")
    except openai.error.AuthenticationError as e:
        #Handle authentication error, e.g. check credentials or log
        retry = False
        print(f"OpenAI API request was not authorized: {e}")
    except openai.error.PermissionError as e:
        #Handle permission error, e.g. check scope or log
        retry = False
        print(f"OpenAI API request was not permitted: {e}")
    except openai.error.RateLimitError as e:
        #Handle rate limit error, e.g. wait or log
        print(f"OpenAI API request exceeded rate limit: {e}")
    except ValueError:
        retry = False
    except KeyError:
        retry = False
    except Exception as e: #pylint: disable=broad-except
        retry = False
        write_unhandled_error(e, "generic_openai_request")
    if retry:
        return generic_openai_request(api_call, *args)
    return []
