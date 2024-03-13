"""Tests file for analyzer module."""
# pylint: disable=missing-function-docstring,missing-class-docstring
import json
from os.path import join as directory_path
from django.conf import settings
from django.test import TestCase, Client
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from analyzer.models import Document, NLPTask, Profile, SystemUser, User, Message
from analyzer.io import views_helper
from data_ingestion.file_handling import FileProcessor

VALID_FILE_DATA = "2021-09-25T15:36:30, Jamie Smith: True that, Mia. Let's not freak out though. Lemme try calling her again" # pylint: disable=line-too-long

class DateFormatTest(TestCase):
    """Checks if dates provided to the date formatter are valid."""
    def test_date_for_hhmm(self):
        """Check date function for hh:mm input"""
        output = views_helper.convert_to_timestamp("2024-01-01", "12:23")
        self.assertEqual(output, "2024-01-01T12:23:00+00:00")

    def test_date_for_hmmss(self):
        """Check date function for hh:mm:ss input"""
        output = views_helper.convert_to_timestamp("2024-01-01", "12:23:05")
        self.assertEqual(output, "2024-01-01T12:23:05+00:00")

    def test_invalid_date(self):
        """Check date function for invalid date."""
        output = views_helper.convert_to_timestamp("dwejijwde", "rf3")
        self.assertEqual(output, "1970-01-01T00:00:00+00:00")

class ApiAcceptFileTestCase(TestCase):

    def setUp(self):
        self.client = Client()
        user = SystemUser.objects.get_or_create(
            user=User.objects.create_user(username='testuser', password='testpassword')
        )[0]
        self.client.login(username='testuser', password='testpassword')
        self.url = reverse('api_accept_file')
        self.document_record = Document.objects.get_or_create(
            file=ContentFile(
                VALID_FILE_DATA,
                name=directory_path(settings.MEDIA_ROOT, "uploaded_documents", "test_accept.txt")
            ),
            display_name="test_accept.txt",
            owner=user, accepted=False,
            is_ingestion_output=False
        )[0]

        self.document = FileProcessor(self.document_record.file.path)
        self.document.process()
        self.path = self.document.file.save(user)

    def test_api_accept_file_success(self):

        data = {
            "file_name": self.path,
            "field_mapping":[
                {"field":"sender","value":"name"},
                {"field":"body","value":"body"},
                {"field":"date","value":"date"},
                {"field":"time","value":"time"}
            ]
        }
        response = self.client.post(self.url, json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["success"], True)
        self.assertIn("Your file has been accepted.", response.json()["message"])

    def test_api_accept_file_no_file_name(self):
        data = {
            "field_mapping":[
                {"field":"sender","value":"name"},
                {"field":"body","value":"body"},
                {"field":"date","value":"date"},
                {"field":"time","value":"time"}
            ]
        }
        response = self.client.post(self.url, json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["success"], False)
        self.assertEqual(response.json()["error"], "No file name was provided.")

    def test_api_accept_file_file_not_found(self):
        data = {
            'file_name': '066acc3a-4979-76de-af90-52a3b73d92cc.txt',
            "field_mapping": [
                {"field":"sender","value":"name"},
                {"field":"body","value":"body"},
                {"field":"date","value":"date"},
                {"field":"time","value":"time"}
            ]
        }
        response = self.client.post(self.url, json.dumps(data), content_type='application/json')

        # Check the response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            "success": False,
            "error": "This file was not found in the database."
        })

    def test_api_accept_file_invalid_field_mapping(self):
        data = {
            "file_name": self.path,
            "field_mapping": [{"field1": "value1", "field2": ""}]
        }
        response = self.client.post(self.url, json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["success"], False)
        self.assertTrue(response.json()["error"])

class ApiRejectFileTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        user = SystemUser.objects.get_or_create(user=User.objects.create_user(
            username='testuser', password='testpassword')
        )[0]
        self.client.login(username='testuser', password='testpassword')
        self.url = reverse('api_reject_file')
        self.document_record = Document.objects.get_or_create(
            file=ContentFile(
                VALID_FILE_DATA,
                name=directory_path(settings.MEDIA_ROOT, "uploaded_documents", "test_reject.txt")
            ),
            display_name="test_reject.txt",
            owner=user,
            accepted=False,
            is_ingestion_output=False
        )[0]

        self.document = FileProcessor(self.document_record.file.path)
        self.document.process()
        self.path = self.document.file.save(user)

    def test_api_reject_file_success(self):

        # Reject the file
        data = {'file_name': self.path}
        response = self.client.post(self.url, json.dumps(data), content_type='application/json')

        # Check the response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            "success": True,
            "message": "Your file has been rejected."
        })

    def test_api_reject_file_no_file_name(self):
        # Send a POST request without file_name
        response = self.client.post(self.url, json.dumps({}), content_type='application/json')

        # Check the response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            "success": False,
            "error": "No file name was provided."
        })

    def test_api_reject_file_file_not_found_invalid_uuid(self):
        # Send a POST request with a non-existing file_name
        data = {'file_name': 'non_existing_file.txt'}
        response = self.client.post(self.url, json.dumps(data), content_type='application/json')

        # Check the response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            "success": False,
            "error": "Invalid file name. Please check your file name and try again."
        })

    def test_api_reject_file_file_not_found(self):
        data = {'file_name': '066acc3a-4979-76de-af90-52a3b73d92cc.txt'}
        response = self.client.post(self.url, json.dumps(data), content_type='application/json')

        # Check the response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            "success": False,
            "error": "This file was not found in the database."
        })

    def test_api_reject_file_invalid_method(self):
        # Send a GET request instead of POST
        response = self.client.get(self.url)

        # Check the response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            "error": "This endpoint only accepts POST requests.",
            "success": False
        })

class UploadFileTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = SystemUser.objects.get_or_create(
            user=User.objects.create_user(username='testuser', password='testpassword')
        )[0]
        self.client.login(username='testuser', password='testpassword')
        self.url = reverse('api_upload_file')

    def test_upload_valid_file(self):
        # Make a POST request to the API endpoint
        # Note: Do not use unformatted data here,
        # as the OpenAI API key is not accessible when it is tested in the pipeline.
        file = SimpleUploadedFile("test_upload.txt", VALID_FILE_DATA.encode(), "text/plain")

        response = self.client.post(self.url, {'file': file})

        # Check if the response is successful
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'], response.json())
        filename = response.json()['file_name']

        # Check if the file record is created in the database
        document = Document.objects.get(file=filename)
        self.assertEqual(document.owner, self.user)

        # Clean up the test file
        document.file.delete()

    def test_upload_invalid_file(self):
        # Create an invalid file

        # Make a POST request to the API endpoint
        file = SimpleUploadedFile("test_upload.txt", b"", "text/plain")

        response = self.client.post(self.url, {'file': file})

        # Check if the response indicates failure
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()['success'])
        self.assertTrue(response.json()['error'])

    def test_upload_no_file(self):
        # Make a POST request to the API endpoint without a file
        response = self.client.post(self.url)

        # Check if the response indicates failure
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()['success'])
        self.assertTrue(response.json()['error'])

    def test_upload_invalid_request_method(self):
        # Make a GET request to the API endpoint
        response = self.client.get(self.url)

        # Check if the response indicates failure
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()['success'])
        self.assertTrue(response.json()['error'])

class LoginTestCase(TestCase):

    def setUp(self):
        self.client = Client()
        self.url = reverse('api_login')
        self.user = User.objects.create_user(username='testuser', password='testpassword')

    def test_login_success(self):
        # Make a POST request to the API endpoint
        response = self.client.post(self.url, json.dumps({
            'username': 'testuser', 'password': 'testpassword'}),
            content_type='application/json'
        )

        # Check if the response is successful
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        self.assertEqual(response.json()['message'], 'Successfully logged in.')

    def test_login_invalid_credentials(self):
        # Make a POST request to the API endpoint with invalid credentials
        response = self.client.post(self.url, json.dumps({
            'username': 'testuser', 'password': 'invalidpassword'
        }), content_type='application/json')

        # Check if the response indicates failure
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()['success'])
        self.assertTrue(response.json()['message'])

    def test_login_no_credentials(self):
        # Make a POST request to the API endpoint without credentials
        response = self.client.post(self.url, json.dumps({}), content_type='application/json')

        # Check if the response indicates failure
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()['success'])
        self.assertTrue(response.json()['message'])

    def test_login_invalid_request_method(self):
        # Make a GET request to the API endpoint
        response = self.client.get(self.url)

        # Check if the response indicates failure
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()['success'])
        self.assertTrue(response.json()['message'])

class MessageTestCase(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = SystemUser.objects.get_or_create(
            user=User.objects.create_user(username='testuser', password='testpassword')
        )[0]
        self.client.login(username='testuser', password='testpassword')
        self.document = Document.objects.get_or_create(file=ContentFile(
            VALID_FILE_DATA,
            name=directory_path(settings.MEDIA_ROOT, "uploaded_documents", "test_message.txt")),
            display_name="test_message.txt",
            owner=self.user,
            accepted=True,
            is_ingestion_output=False
        )[0]

    def test_message_success(self):
        # GET a message
        profile = Profile.objects.get_or_create(name="Jamie Smith")[0]
        message = Message.objects.get_or_create(
            date="2021-09-25T15:36:30",
            body="True that, Mia. Let's not freak out though. Lemme try calling her again",
            source=self.document,
            owner=profile
        )[0]

        nlp_data = {
            'risk': 0.5,
            'sentiment': 0.5,
            'topics': [['key', 'value']]
        }
        NLPTask.objects.get_or_create(message=message, result=json.dumps(nlp_data))

        url = reverse('api_message', kwargs={'message_id': message.pk})
        response = self.client.get(url, {'file_name': self.document.file.name})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            'pending': False,
            'document_name': 'test_message.txt',
            'owner_name': 'Jamie Smith',
            'message_body': "True that, Mia. Let's not freak out though. Lemme try calling her again", # pylint: disable=line-too-long
            'message_date': '2021-09-25T15:36:30Z',
            'message_risk_score': 'LOW (0.5)',
            'message_sentiment': 'slightly positive',
            'message_source': str(self.document.uuid),
            'concept_analysis_data': [{'concept': 'value', 'keyword': 'key'}],
        })

    def test_message_non_existant(self):
        # GET a message
        url = reverse('api_message', kwargs={'message_id': 42789872398})
        response = self.client.get(url, {'file_name': self.document.file.name})
        self.assertEqual(response.status_code, 404)

class ChatbotTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = SystemUser.objects.get_or_create(
            user=User.objects.create_user(username='testuser', password='testpassword')
        )[0]
        self.client.login(username='testuser', password='testpassword')
        self.url = reverse('api_chatbot')

    def test_chatbot_success(self):
        # Make a POST request to the API endpoint
        response = self.client.post(self.url, json.dumps({
            'document_id': 'dummy_id',
            'user_messages': [
                {'role': 'user', 'content': 'Hello, chatbot.'}
            ],
            'mock': True
        }), content_type='application/json')

        # Check if the response is successful
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        self.assertEqual(response.json()['messages'], {
            "role": "assistant",
            "content": "A reply from the chatbot."
        })

    def test_chatbot_invalid_request(self):
        # Make a POST request to the API endpoint with invalid messages
        response = self.client.post(self.url, "Hello world", content_type='application/json')

        # Check if the response indicates failure
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()['success'])
        self.assertTrue(response.json()['error'])

    def test_chatbot_no_messages(self):
        # Make a POST request to the API endpoint without messages
        response = self.client.post(
            self.url,
            json.dumps({'mock': True}),
            content_type='application/json'
        )

        # Check if the response indicates failure
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()['success'])
        self.assertTrue(response.json()['error'])

    def test_chatbot_invalid_request_method(self):
        # Make a GET request to the API endpoint
        response = self.client.get(self.url)

        # Check if the response indicates failure
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()['success'])
        self.assertTrue(response.json()['error'])
