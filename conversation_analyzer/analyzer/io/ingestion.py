'''I/O helpers for data ingestion.'''
import json
import os
from typing import Any, TextIO
from django.conf import settings
from analyzer.io.common import PendingRecord
from analyzer.models import Document, SystemUser

def get_openai_request_config() -> Any:
    '''Loads the request configuration for OpenAI from the static files directory.'''
    with open(os.path.join(settings.STATIC_DIR, 'openAIRequest.json'), 'r', encoding='utf8') as f:
        return json.load(f)

def get_saves_write_handle(
    filename: str,
    uploading_user: SystemUser
) -> tuple[TextIO, PendingRecord[Document]]:
    '''
    Writes saves from data ingestion to a designated location,
    pending record should be confirmed once the file write is complete.
    '''
    uuid, _ext = os.path.splitext(filename.split("/")[-1])
    path = os.path.join(settings.MEDIA_ROOT, 'ingestion_saves', uuid)
    # pylint: disable=consider-using-with
    file = open(path, 'w', encoding='utf8')
    return file, PendingRecord(Document(file=path, display_name=filename,
                                        is_ingestion_output=True, owner=uploading_user))
