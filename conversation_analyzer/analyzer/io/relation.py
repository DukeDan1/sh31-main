"""Helper function for relations between users."""
from analyzer.models import Document, Message

def get_document_profiles(document):
    """Gathers names of all people mentioned in a document."""
    all_document_profiles = set(message.owner
        for message in Message.objects.filter(source=document))
    return all_document_profiles

def set_profile_relation(profile):
    """Gathers and then sets profile relations."""
    related_profiles = set()
    for document in Document.objects.all():
        document_profiles = get_document_profiles(document)
        if profile not in document_profiles:
            continue
        document_profiles.discard(profile)
        related_profiles |= document_profiles
    profile.related_profiles.add(*related_profiles)
