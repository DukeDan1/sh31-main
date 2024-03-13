'''All interactions with NLPTask and running the NLP should go here.'''
import json
import sys
from analyzer.io.common import AsyncPendingRecord
from analyzer.models import Message, NLPTask, Profile
from nlp import nlp

if 'makemigrations' not in sys.argv and 'migrate' not in sys.argv:
    NLP_ANALYZER = nlp.NLPAnalyzer()


class NLPTaskRecordManager:
    '''Manages selection and fulfillment of NLPTasks.'''

    def __init__(self, selector_pk):
        self.selector_pk = selector_pk

    def selector(self):
        '''Selects the correct task to fulfill.'''
        return NLPTask.objects.filter(message__in=Message.objects
                                      .filter(pk=self.selector_pk)).first()

    def fulfill(self, model, fulfill_value):
        '''Fulfills the task.'''
        model.result = fulfill_value
        return model

def run_nlp_on_messages(messages):
    '''Instantiates tasks to process messages with NLP.'''
    sentences = []
    pending_records = []
    for message in messages:
        if not NLPTask.objects.filter(message=message).exists():
            NLPTask(message=message, result=None).save()
            runner = NLPTaskRecordManager(message.pk)
            sentences.append(message.body)
            pending_records.append(AsyncPendingRecord(runner.fulfill, runner.selector))
    threads = NLP_ANALYZER.analyze_pooled(sentences, pending_records)
    return threads

def get_messages_nlp_progress(messages):
    '''Gets the progress of document processing in percentage.'''
    tasks = NLPTask.objects.filter(message__in=messages)
    if len(tasks) == 0:
        return 100
    return len(tasks.exclude(result=None)) * 100 / len(tasks)

def wait_nlp_tasks(messages):
    '''Only returns a list of NLP results if all of them are completed'''
    nlp_results = []
    has_tasks_pending = NLPTask.objects.filter(message__in=messages, result=None).exists()
    if not has_tasks_pending:
        for message_obj in messages:
            results = json.loads(NLPTask.objects.get(message=message_obj).result)
            nlp_results.append(results)
    return nlp_results, has_tasks_pending

def get_profile_from_topic(topic):
    '''Gets an appropriate profile for a given topic, creates it if needed.'''
    if topic['concept'] != 'PERSON':
        return None

    full_name = topic['keyword']
    full_name_profile = Profile.objects.filter(name__startswith=full_name)
    if full_name_profile.exists():
        return full_name_profile.first()

    first_name = topic['keyword'].split()[0]
    first_name_profile = Profile.objects.filter(name=first_name)
    if first_name_profile.exists():
        first_name_profile.name = full_name
        first_name_profile.save()
        return first_name_profile

    new_profile = Profile.objects.create(name=full_name)
    return new_profile
