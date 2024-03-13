'''Population script for Django models, for testing and demonstration.'''
# pylint: disable=wrong-import-position
from collections.abc import Iterable
from typing import Any, Generator, TypeVar

import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'conversation_analyzer.settings')
import django
from django.db import models
django.setup()
from django.contrib.auth.models import User
from analyzer.models import Document, Message, Profile, SystemUser

def populate():
    '''Populates each of the defined models with at least one instance.'''
    #all(populate_profiles())
    all(populate_users())
    #passwd_document, *_ = populate_documents(regular_user, normal_user,
    #    john_profile, stephen_profile)
    #all(populate_messages(passwd_document, john_profile))

def populate_documents(
    first_user: User,
    second_user: User,
    first_profile: Profile,
    second_profile: Profile,
    ) -> Iterable[Document]:
    '''Populates documents and returns them, arguments are for placeholders.'''
    passwd, shadow = construct_from_dict(Document.objects, [
        ({'file': '/etc/passwd', 'display_name': 'Password'}, {'pk': 0, 'owner': first_user}),
        ({'file': '/etc/shadow', 'display_name': 'Shadow'}, {'pk': 1, 'owner': second_user}),
    ])
    passwd.mentioned_profiles.add(first_profile, second_profile)
    shadow.mentioned_profiles.add(second_profile)
    return passwd, shadow

def populate_messages(
    source: Document,
    owner: Profile
    ) -> Iterable[Message]:
    '''Populates messages and returns them.'''
    message, *rest = construct_from_dict(Message.objects, [
        ({
            'body': 'How are you?',
        }, {'date': '2020-01-01T00:00:00+00:00', 'source': source, 'owner': owner})
    ])
    return message, *rest

def populate_profiles() -> Iterable[Profile]:
    '''Populates profiles and returns them.'''
    john, stephen, william, *rest = construct_from_dict(Profile.objects, [
        ({
            'name': 'John Johnson',
            'note': 'He is a person.',
        }, 0),
        ({
            'name': 'Stephen Stephenson',
            'note': 'He is the person.',
        }, 1),
        ({
            'name': 'William Williamson',
            'note': 'He is a third person.',
        }, 2),
    ])
    stephen.related_profiles.add(john)
    william.related_profiles.add(john, stephen)
    return john, stephen, william, *rest

def populate_users() -> Iterable[User]:
    '''Populates users and returns them.'''
    password = ('pbkdf2_sha256$600000$XlaWM1BuBN88DWHwYyGuOr$' +
                'GJSiwJSdmpSlC9Wwg+kQb8+GD+HjGpyxOgm1vmR7Ljs=')
    django_users = construct_from_dict(User.objects, [
        ({}, {
            'username': 'user',
            'password': password,
            'last_login': '1970-01-01T00:00:00+00:00',
        }),
        ({ 'is_superuser': True, 'is_staff': True }, {
            'username': 'admin',
            'password': password,
            'last_login': '1970-01-01T00:00:00+00:00',
        }),
    ])
    for user in django_users:
        SystemUser(user=user).save()
    return ()

T = TypeVar('T', bound=models.Model)

def construct_from_dict(
    model_manager: models.Manager[T],
    props: list[tuple[dict[str, Any], dict|Any]],
    ) -> Generator[T, None, None]:
    '''Constructs and saves records to the database.

    Arguments:
    model_manager -- manager of the model to construct.
    prop          -- tuples of column keys mappings to values and the selection keys.
                     If the selection key is not a dict, it will be used as a primary key.
    '''
    for prop_dict, pk in props:
        keys = pk if isinstance(pk, dict) else {'pk': pk}
        record = model_manager.get_or_create(**keys)[0]
        for key, value in prop_dict.items():
            setattr(record, key, value)
        record.save()
        yield record

if __name__ == '__main__':
    populate()
