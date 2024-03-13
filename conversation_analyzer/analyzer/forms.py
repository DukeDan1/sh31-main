'''Model forms for user input in Django.'''

from django import forms
from django.contrib.auth.models import User
from analyzer.models import Document

class DocumentUploadForm(forms.ModelForm):
    '''Main document upload for data ingestion.'''
    file = forms.FileField(label='')

    class Meta:
        '''Metadata for DocumentUploadForm.'''
        model = Document
        fields = ('file',)
        widget = {'display_name': forms.HiddenInput()}

class UserProfileForm(forms.ModelForm):
    '''Main form for user registration.'''
    password = forms.CharField(widget=forms.PasswordInput())

    class Meta:
        '''Metadata for UserProfileForm.'''
        model = User
        fields = ('username', 'password')
