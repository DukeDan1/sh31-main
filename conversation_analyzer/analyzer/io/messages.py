'''I/O helpers for messages page.'''
from analyzer.models import Document, Message, SystemUser

NIL_UUID = '00000000-0000-0000-0000-000000000000'

def get_messages_by_uuid(user, document_uuid):
    '''
    Gets message from the document with the given UUID.
    NIL_UUID will get all of the documents that are owned by the user.
    '''
    if document_uuid == NIL_UUID:
        owned_documents = get_owned_documents(user)
        return Message.objects.filter(source__uuid__in=owned_documents)
    return Message.objects.filter(source__uuid=document_uuid).order_by('date')

def get_owned_documents(user):
    '''Gets all owned document for the user, all documents for superuser.'''
    sys_user = SystemUser.objects.get(user=user)
    all_documents = Document.objects.filter(is_ingestion_output=True, accepted=True)
    if not user.is_superuser:
        all_documents = all_documents.filter(owner=sys_user)
    return all_documents
