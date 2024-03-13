'''I/O Helper for plot.py'''
from collections import Counter
from analyzer.models import Message
from analyzer.io import query_helper
from analyzer.io.nlp import wait_nlp_tasks
from django.db.models import F, ExpressionWrapper, fields, Subquery, OuterRef, Value, Count, Avg
import numpy as np

def get_owner_topic_risk_list(messages):
    '''This method gets the owner, topic and risk for messages.'''
    nlp_results, has_tasks_pending = wait_nlp_tasks(messages)
    owner_topics_risk_dict = []
    for message, nlp_result in zip(messages, nlp_results):
        for topic in nlp_result['topics']:
            owner_topics_risk_dict.append({
                'owner': message.owner.name,
                'topic': topic,
                'risk': round(nlp_result['risk'], 2)
            })
    return owner_topics_risk_dict, has_tasks_pending

def get_doc_topics(document):
    '''This method gets the topics
    for each message in a document'''
    query = query_helper.Queries()
    message_topics, topics_pending = query.get_nlp_data("source",document, 'topics')
    singular_topics = []
    for topics in message_topics:
        if len(topics)>0:
            for topic in topics:
                singular_topics.append(topic[0])
    unique_topics = set(singular_topics)
    return list(unique_topics), topics_pending

def get_doc_sentiment(document):
    '''This method gets the sentiment
    for each message in the document'''
    query = query_helper.Queries()
    sentiment, pending = query.get_nlp_data("source", document, 'sentiment')
    return round_float(sentiment), pending

def get_profiles_in_doc(document):
    '''This method gets the Profiles
    of conversation Particpants and
    gets there average risk'''
    profiles_in_doc = set(message.owner for message in Message.objects.filter(source=document))
    query = query_helper.Queries()
    means = []
    pending = False
    for owner in profiles_in_doc:
        risk, doc_pending = query.get_nlp_data("owner", owner, 'risk')
        risk_float = round_float(risk)
        means.append(np.mean(np.array(risk_float)))
        if doc_pending:
            pending = doc_pending
    return means, pending

def get_doc_risk(document):
    '''This method gets the risk
    for each message in a document'''
    query = query_helper.Queries()
    risk, pending = query.get_nlp_data("source", document, 'risk')
    return round_float(risk), pending

def doc_time_diff(document):
    '''This method calculates
    the time between messages in minutes'''
    message_objs = Message.objects.filter(source=document).order_by('date')
    sub_query = Message.objects.filter(date__lt=OuterRef('date'),
            source=document).order_by('-date').values('date')[:1]
    response_times = message_objs.annotate(
        prev_time=Subquery(sub_query),
            time_difference=ExpressionWrapper(
            (F('date')-F('prev_time'))/ Value(3600000),
            output_field=fields.FloatField()
            )).values_list('time_difference', flat=True
                           ).exclude(time_difference=None)
    return round_float(list(response_times))

def round_float(query_result):
    '''This method rounds a float
    to 2 decimal places'''
    return [round(query_element, 2) for query_element in query_result]

def get_number_of_messages(document):
    '''This method gets the number
    of messages for a document'''
    return Message.objects.filter(source=document).count()

def get_number_of_profiles(document):
    '''This method gets the number
     of profiles for a document'''
    return Message.objects.filter(source=document).values('owner').distinct().count()

def get_profile_avg_message(document):
    '''This method gets the average number
    of messages per profile in a document'''
    messages_per_owner = Message.objects.filter(source=document).values(
        'owner').annotate(message_count=Count('id'))
    avg_messages = messages_per_owner.aggregate(avg_message=Avg(
        'message_count'))['avg_message']
    return avg_messages

def profiles_risk(messages):
    '''Gets the risk for every profile
    in the document'''
    profiles = set()
    profiles_risk_dict = {}
    profiles_in_dict = []
    for single_message in messages:
        profiles.add(single_message.owner.name)
    nlp_results, has_tasks_pending = wait_nlp_tasks(messages)
    for message, nlp_result in zip(messages, nlp_results):
        if message.owner.name in profiles_in_dict:
            profiles_risk_dict[message.owner.name].append(nlp_result['risk'])
        else:
            profiles_risk_dict[message.owner.name] = [nlp_result['risk']]
            profiles_in_dict.append(message.owner.name)
    return profiles_risk_dict, has_tasks_pending

def get_document_profile_topics(messages):
    '''gets the document, owner and topic for each message'''
    nlp_results, has_tasks_pending = wait_nlp_tasks(messages)
    owner_topics = []
    for message, nlp_result in zip(messages, nlp_results):
        for topic in nlp_result['topics']:
            owner_topics.append({'document':message.source.display_name,
                                 'owner':message.owner.name,
                                 'topic':topic})
    return owner_topics, has_tasks_pending

def change_key_to_topic(owner_topics):
    '''Changes the dict from the docuemnt being the key to
    the topics being the keys'''
    unique_topics = set()
    for owner_topic_element in owner_topics:
        unique_topics.add(owner_topic_element['topic'][0])
    topic_key_dict = {}
    topics_in_dict =[]
    topic_document_count = Counter()
    for owner_topic_dict in owner_topics:
        if owner_topic_dict['topic'][0] in topics_in_dict:
            if [owner_topic_dict['document'],
                owner_topic_dict['owner']] not in topic_key_dict[
                owner_topic_dict['topic'][0]]:

                topic_key_dict[owner_topic_dict['topic'][0]].append(
                    [owner_topic_dict['document'], owner_topic_dict['owner']])
                topic_document_count[(owner_topic_dict['topic'][0],
                                    owner_topic_dict['document'])]+=1
        else:
            topic_key_dict[owner_topic_dict['topic'][0]] = [[owner_topic_dict['document'],
                                                             owner_topic_dict['owner']]]
            topic_document_count[(owner_topic_dict['topic'][0], owner_topic_dict['document'])]+=1
            topics_in_dict.append(owner_topic_dict['topic'][0])
    return remove_unshared_topics(topic_key_dict, topic_document_count)

def remove_unshared_topics(topic_key_dict,topic_document_count):
    '''Removes topics from the dictionary that
    are not common between documents'''
    shared_topics = {}
    for topic, owner_and_doc in topic_key_dict.items():
        if len(owner_and_doc) >1:
            combined = combine_profiles(topic, owner_and_doc, topic_document_count)
            if len(combined) >1:
                shared_topics[topic] = combined
    return shared_topics

def combine_profiles(topic,doc_profiles, topic_document_count):
    '''Combines the profles into one string if multiple
    profiles mention a topic in a document'''
    combined_profiles = []
    to_skip = []
    for index, doc_profile in enumerate(doc_profiles):
        combine_profile = []
        if topic_document_count[(topic,doc_profile[0])]>1 and doc_profile not in to_skip:
            combine_profile.append(doc_profile[1])
            for pos in range(index+1,len(doc_profiles)):
                if doc_profiles[pos][0] == doc_profile[0]:
                    combine_profile.append(doc_profiles[pos][1])
                    to_skip.append(doc_profiles[pos])
            combined_profiles.append([doc_profile[0], ' and '.join(combine_profile)])

        elif doc_profile not in to_skip:
            combined_profiles.append(doc_profile)
    return combined_profiles
