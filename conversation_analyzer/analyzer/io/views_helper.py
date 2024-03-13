'''I/O helpers for view function.'''
import os
from os.path import join as directory_join
import json
from datetime import datetime
from analyzer.models import Document, Message, Profile, SystemUser
from analyzer.io.messages import get_messages_by_uuid, get_owned_documents, NIL_UUID
from analyzer.io.nlp import run_nlp_on_messages, wait_nlp_tasks
from analyzer.io.common import PendingRecord
from data_ingestion.file_handling import JSONFile
from graph import plot
import pytz
import openai
from conversation_analyzer import settings


def read_json_from_file(filename: str):
    '''Reads a JSON file verbatim'''
    file = JSONFile(filename)
    file.read()
    file.parse()
    return file.parsed_data

def delete_pending_documents(request):
    '''Deletes all pending documents that do not have a corresponding accepted record.'''
    system_user = SystemUser.objects.get(user=request.user)

    if request.user.is_superuser:
        all_documents = Document.objects.filter(is_ingestion_output=False)
    else:
        all_documents = Document.objects.filter(owner=system_user, is_ingestion_output=False)

    # Get all documents that do not have a corresponding accepted record
    all_accepted_documents = all_documents.filter(accepted=False)

    for document in all_accepted_documents:
        uuid, _ext = os.path.splitext(document.file.path.split("/")[-1])
        record = PendingRecord(Document.objects.get(uuid=uuid))
        record.reject()

def populate_message(uuid, field_mapping, parsed_json):
    '''Interprets the parsed JSON as messages.'''
    for row in parsed_json:
        if field_mapping.get("date") and field_mapping.get("time"):
            row["timestamp"] = convert_to_timestamp(
                row[field_mapping["date"]], row[field_mapping["time"]]
            )
            field_mapping["timestamp"] = "timestamp"

        body = row[field_mapping["body"]]
        if isinstance(body, dict):
            body = list(body.values())[0]

        # Problem: there is no support for different people with the same name.
        # How can we identify when this is the case?
        message = Message(date=row[field_mapping["timestamp"]], body=body,
                        source=Document.objects.get(uuid=uuid),
                        owner=Profile.objects.get_or_create(
                            name=row.get(field_mapping["sender"])
                            if row.get(field_mapping["sender"]) is not None
                            else "Unknown Sender"
                        )[0])

        message.save()

def parse_field_mapping(in_fields) -> dict:
    """Parses user selections for field mapping and returns a dictionary
    which maps the user selection to the field name of the file."""
    fields_as_dict =  {
        entry["field"]: entry["value"]
        for entry in in_fields
        if entry.get("value") is not None and entry.get("value") != ""
    }

    return fields_as_dict

def convert_to_timestamp(date_str, time_str) -> str:
    """Convert two strings for date and time into the standard timestamp format."""
    if len(time_str) == 5:
        time_str += ":00"
    try:
        datetime_str = f"{date_str} {time_str}"
        datetime_obj = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S')
        utc_datetime = datetime_obj.replace(tzinfo=pytz.UTC)
        timestamp = utc_datetime.isoformat()
    except ValueError:
        timestamp = "1970-01-01T00:00:00+00:00"
    return timestamp

def graph_logic(user, document_uuid):
    '''This method handles the
    logic for single document or
    multiple document graphs and the
    progress bar'''
    messages = get_messages_by_uuid(user, document_uuid)
    if not messages.exists():
        return plot.empty_graph_analysis(5)

    run_nlp_on_messages(messages)
    nlp_results, has_tasks_pending = wait_nlp_tasks(messages)
    if has_tasks_pending:
        return None

    if document_uuid != NIL_UUID:
        pop_dict = plot.populate_nlp_dict(nlp_results)
        graphs,description = plot.singular_doc_analysis(messages, pop_dict)
    else:
        documents = get_owned_documents(user)
        graphs, description = plot.all_doc_analysis(documents, messages)
    return graphs, description

def get_profile_risk_stat(profile):
    '''Calculates the average risk for the given profile.'''
    message_objs = Message.objects.filter(owner=profile)
    nlp_results, _ = wait_nlp_tasks(message_objs)
    populated_dict = plot.populate_nlp_dict(nlp_results)

    risks = populated_dict['Risk']
    average_risk = sum(risks) / len(risks) if any(risks) else 0
    return average_risk

def chatbot_request(user_messages, parsed_file, mock=False):
    """Makes a request to the chatbot. If mock is True, returns a mock response."""
    if mock:
        return {
            "role": "assistant",
            "content": "A reply from the chatbot."
        }

    with open(
        directory_join(settings.STATIC_DIR, 'openAIRequestAnalysis.json'),
        'r',
        encoding='utf8'
    ) as f:
        file_data = json.loads(f.read())

        request = file_data['chatbot']
        request['messages'].append({
            'role': 'user',
            'content': json.dumps(parsed_file)
        })
        request['messages'].extend(user_messages)


        print("[LOG] Making OpenAI request...")
        response = openai.ChatCompletion.create(**request)

        return response["choices"][0]["message"]

def get_user(request):
    '''Gets the User'''
    return SystemUser.objects.get(user=request.user)
