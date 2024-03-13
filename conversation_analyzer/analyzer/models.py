'''ORM models for Django.'''

import uuid

from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse


class Profile(models.Model):
    ''' Represents a person who either made a message, or is mentioned.'''
    name = models.CharField(max_length=256)
    note = models.TextField()

    related_profiles = models.ManyToManyField('self')

    @staticmethod
    def get_mock():
        '''Creates or gets a mock Profile.'''
        return Profile.objects.get_or_create(pk=1, name='John', note='Hello')[0]

    def __str__(self):
        return str(self.name)

def uuid_path(instance: 'Document', filename: str) -> str:
    '''Returns a media store path with the filename replaced by a UUID.'''
    uuid_for_file = uuid.uuid4()
    instance.uuid = uuid_for_file
    file_path = f'uploaded_documents/{uuid_for_file}.{filename.split(".")[-1]}'
    return file_path

class SystemUser(models.Model):
    '''Represents a user profile for the database.'''
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    query_tracking_enabled = models.BooleanField(default=True)

    @staticmethod
    def get_mock():
        '''Creates or gets a mock SystemUser.'''
        django_user = User.objects.get_or_create(
            username='user', password='password',
            last_login='1970-01-01T00:00:00+00:00'
        )[0]
        return SystemUser.objects.get_or_create(pk=1, user=django_user)[0]

    def __str__(self):
        return str(self.user)


class Document(models.Model):
    '''Represents a document in the filesystem for any format.'''
    file = models.FileField(upload_to=uuid_path)
    uuid = models.UUIDField(default=uuid.uuid4, primary_key=True)
    display_name = models.CharField(max_length=4096)
    accepted = models.BooleanField(default=False)
    is_ingestion_output = models.BooleanField(default=False)

    owner = models.ForeignKey(SystemUser, on_delete=models.CASCADE)
    mentioned_profiles = models.ManyToManyField(Profile)

    openai_data = models.JSONField(null=True)

    @staticmethod
    def get_mock():
        '''Creates or gets a mock Document.'''
        return Document.objects.get_or_create(
            pk=1,
            file='/etc/passwd', display_name='Password',
            owner=SystemUser.get_mock()
        )[0]

    def __str__(self):
        return self.file.name

    def get_url(self):
        '''Returns the URL for the document.'''
        return reverse('messages_view', args=[str(self.uuid)])


class RecentActivity(models.Model):
    '''Represents the users recent activity on a document'''
    user = models.ForeignKey(SystemUser, on_delete=models.CASCADE)
    document = models.ForeignKey(Document, null=True, on_delete=models.CASCADE)
    profile = models.ForeignKey(Profile, null=True, on_delete=models.CASCADE)
    activity_time = models.DateTimeField(auto_now=True)

    def __str__(self):
        formatted_time = self.activity_time.strftime('%I:%M%p %Z on %b %d, %Y')
        name = self.document.display_name if self.profile is None else self.profile.name
        return f'You recently visited {name} at {formatted_time}.'

class Message(models.Model):
    '''Represents an analyzed message that is extracted from the document.'''
    date = models.DateTimeField()
    body = models.TextField()

    source = models.ForeignKey(Document, on_delete=models.CASCADE)
    owner = models.ForeignKey(Profile, on_delete=models.CASCADE)

    @staticmethod
    def get_mock():
        '''Creates or gets a mock Message.'''
        return Message.objects.get_or_create(
            date='2020-01-01T00:00:00+00:00',
            body='message body', source=Document.get_mock(),
            owner=Profile.get_mock()
        )[0]

    def __str__(self):
        return 'Message #' + str(self.pk)


class NLPTask(models.Model):
    '''Represents a background NLP task that completes in the future.'''
    message = models.OneToOneField(Message, on_delete=models.CASCADE)
    result = models.TextField(null=True)

    @staticmethod
    def get_mock():
        '''Creates or gets a mock NLPTask.'''
        return NLPTask.objects.get_or_create(message=Message.get_mock())[0]

    def __str__(self):
        return str(self.result)
