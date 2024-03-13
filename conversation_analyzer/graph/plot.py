'''Plotting functions using Plotly.'''
from plotly.offline import plot
from analyzer.models import Message
from graph import plot_helper
import plotly.graph_objs as go
import plotly.colors as plc
import numpy as np

def mapping_styles(marker_color):
    '''Creates common style for mapping plots.'''
    return {
            'mode': 'markers+text', 'hoverinfo': 'none',
            'textposition': 'top center', 'showlegend': False,
            'textfont': {'size': 12, 'color': 'black'},
            'marker': {'color': marker_color}
        }

def select_random_coordinates(count, opposite):
    '''
    Generates count number of random sparse coordinates in column form,
    and negates them if opposite.
    '''
    sign_multiplier = 1 - int(opposite) * 2
    chosen_coordinates = np.array([[sign_multiplier, sign_multiplier]])
    while len(chosen_coordinates) < count:
        random_coordinates = np.random.randint(10, size=2) * sign_multiplier
        min_dists = np.linalg.norm(chosen_coordinates - random_coordinates, axis=1)
        if np.min(min_dists) >= 2:
            chosen_coordinates = np.append(chosen_coordinates, random_coordinates[None,:], axis=0)
    return {
        'x': chosen_coordinates[:, 0],
        'y': chosen_coordinates[:, 1]
    }

def relationship_graph(messages):
    '''This function creates a network graph for Profile and topic relations'''
    messages_in_doc, pending = plot_helper.get_owner_topic_risk_list(messages)
    unique_owners = np.sort(np.array(list({message['owner'] for message in messages_in_doc})))
    unique_topics = np.sort(np.array(list({message['topic'][0] for message in messages_in_doc})))
    if pending:
        return [empty_graph(), pending]

    fig = go.Figure()

    name_points = {'text': unique_owners} | select_random_coordinates(len(unique_owners), False)
    topic_points = {'text': unique_topics} | select_random_coordinates(len(unique_topics), True)

    for message in messages_in_doc:
        name_coordinates_i = np.searchsorted(unique_owners, message['owner'])
        topic_coordinates_i = np.searchsorted(unique_topics, message['topic'][0])
        fig.add_trace(go.Scatter(
            x=[name_points['x'][name_coordinates_i], topic_points['x'][topic_coordinates_i]],
            y=[name_points['y'][name_coordinates_i], topic_points['y'][topic_coordinates_i]],
            name=message['risk'],
            mode='lines'
        ))

    fig.add_trace(go.Scatter(**name_points, **mapping_styles('yellow')))
    fig.add_trace(go.Scatter(**topic_points, **mapping_styles('orange')))

    fig.update_layout(
        title='Mentioned Topics By Participants',
        showlegend=False,
        legend_title='Risk',
        xaxis={'visible': False},
        yaxis={'visible': False},
        font_family ="Roboto"
    )
    return [plot(fig, include_plotlyjs=False, output_type='div'), pending]

def get_graph_risk_and_sentiment(dict_analysis):
    '''This method creates the graphs for risks and sentiment'''
    fig_scatter = go.Figure(go.Scatter(x=dict_analysis["ID"],
                                       y=dict_analysis["Sentiment"],
                                       mode='lines', name="Sentiment",
                                       opacity=0.8, marker_color="green",
                                       hovertemplate='%{y}'),)
    fig_scatter.add_trace(go.Scatter(x=dict_analysis["ID"],
                                     y=dict_analysis["Risk"],
                                     mode='lines', name="Risk",
                                     opacity=0.8, marker_color="red",
                                     hovertemplate='%{y}'))
    fig_scatter.update_layout(title="Sentiment And Risk Ratings Over Messages",
                              xaxis_title="Message ID",
                              yaxis_title="Rating",
                              font_family='Roboto')
    return plot(fig_scatter, include_plotlyjs=False, output_type='div')

def wassa_graphs(dict_analysis):
    '''Method creates a graph showing the change in emotions
      from the Text Regression on Emotional Presence'''
    fig = go.Figure()
    for emotion in ('Joy', 'Sad', 'Anger', 'Fear'):
        fig.add_trace(go.Scatter(x=dict_analysis['ID'],
                                 y=dict_analysis[emotion],
                                 mode='lines',
                                 name=emotion,
                                 hovertemplate='%{y}'))
    fig.update_layout(title='Emotions Over Messages',
                      xaxis_title='Message ID',
                      yaxis_title='Score',
                      font_family='Roboto')
    return plot(fig, include_plotlyjs=False, output_type='div')

def wassa_ridgeplot(dict_analysis):
    '''Creates a ridgeplot showing the distribution
    of WASSA emotions in the document'''
    fig = go.Figure()
    for emotion in ('Sad','Anger','Joy','Fear'):
        fig.add_trace(go.Violin(x=dict_analysis[emotion],
                      name=emotion,
                      box_visible=True,
                      meanline_visible=True))
    fig.update_traces(orientation='h', side='positive',
                      width = 3, points=False, hoverinfo='skip')
    fig.update_layout(title ="Emotion Distribution",
                      xaxis_showgrid=False,
                      xaxis_zeroline=False,
                      font_family='Roboto',
                      legend= {'x':0, 'y':-0.1,
                               'traceorder':'normal',
                               'orientation':'h'},
                      yaxis={'showline':False,
                             'zeroline':False,
                             'showgrid':False,
                             'showticklabels':False})
    return plot(fig, include_plotlyjs=False, output_type='div')

def populate_nlp_dict(messages):
    '''This method populates a dictionary for Graphical Analysis'''

    populated_dict = {"ID":[], "Joy":[], "Sad":[], "Anger":[], "Fear":[], "Sentiment":[], "Risk":[]}
    for index, message in enumerate(messages):
        populated_dict["ID"].append(index + 1)
        populated_dict["Sad"].append(message["sad_extreme"])
        populated_dict['Anger'].append(message["anger_extreme"])
        populated_dict['Fear'].append(message["fear_extreme"])
        populated_dict['Joy'].append(message["joy_extreme"])
        populated_dict["Sentiment"].append(message["sentiment"])
        populated_dict["Risk"].append(message["risk"])
    return populated_dict

def cluster_graph(dataframe):
    '''Plots words in clusters predicted by K-Means'''
    predicted_cluster = dataframe['predicted_cluster']
    fig = go.Figure()

    color_scale = plc.qualitative.Set1
    for cluster in predicted_cluster.unique():
        cluster_data = dataframe[dataframe["predicted_cluster"] == cluster]
        fig.add_trace(go.Scatter(
            x=cluster_data["Risk"],
            y=cluster_data["Vector"],
            mode='markers',
            name=f'Cluster {cluster}',
            marker={"size": 8, "color": color_scale[
                cluster % len(color_scale)]},
            text=cluster_data["true_label"],
            hoverinfo='text'
        ))
    fig.update_layout(
        title="K-means Clustering of Risk and Keywords",
        xaxis={"title": "Risk"},
        yaxis={"title": "Word Similarity"},
        legend={"title": "Legend"},font_family='Roboto')
    return plot(fig, include_plotlyjs=False, output_type="div")

def risk_dist(documents):
    '''Creates a ridgeplot
    of Risk for every document'''
    doc_pend = False
    checked_docs = [doc for doc in documents if
                    check_has_messages(doc)]
    all_doc_name_freq = []
    risk_list = []
    for doc in checked_docs:
        message_risks_in_doc, doc_pend = plot_helper.get_doc_risk(doc)
        if doc_pend:
            return [empty_graph(), doc_pend]
        risk_list.append(message_risks_in_doc)
        all_doc_name_freq.append([doc.display_name
                          ]*len(message_risks_in_doc))
    fig = go.Figure()
    colors = plc.n_colors('rgb(5, 200, 200)'
                          , 'rgb(200, 10, 10)',
                          len(documents) + 1,
                          colortype='rgb')

    for doc,mess_risk,color in zip(all_doc_name_freq,
                                   risk_list,
                                   colors):
        if len(mess_risk)>0:
            fig.add_trace(go.Violin(x=mess_risk,
                      name=doc[0],
                      line_color=color,
                      box_visible=True,
                      meanline_visible=True))

    fig.update_traces(orientation='h', side='positive',
                      width = 3, points=False, hoverinfo='skip')
    fig.update_layout(title ="Document Risk Distribution",
                      xaxis_showgrid=False,
                      xaxis_zeroline=False,
                      legend= {'x':0, 'y':-0.1,
                               'traceorder':'normal',
                               'orientation':'h'},
                      yaxis={'showline':False,
                             'zeroline':False,
                             'showgrid':False,
                             'showticklabels':False},font_family='Roboto')
    return [plot(fig, include_plotlyjs=False, output_type='div'), doc_pend]

def document_topics_graph(documents):
    '''Displays each topic mentioned
    in Each Document grouped by Document'''
    doc_pending = False
    checked_docs = [doc for doc
            in documents
            if check_has_messages(doc)]
    doc_topics = {}
    for doc in checked_docs:
        doc_topic, doc_pending = plot_helper.get_doc_topics(doc)
        doc_topics[doc.display_name] = doc_topic
        if doc_pending:
            return [empty_graph(), doc_pending]
    fig = go.Figure()
    colors = [f'rgb({np.random.randint(0, 255)},'
              f'{np.random.randint(0, 255)},'
              f'{np.random.randint(0, 255)})'
          for _ in range(len(doc_topics))]

    for index, (document, words) in enumerate(
        doc_topics.items()):
        theta = 2 * np.pi * np.random.rand(
            len(words))
        r = 0.2 * np.sqrt(np.random.rand(
            len(words)))
        x = (index +1) + r * np.cos(theta)
        y = 0 + r * np.sin(theta)
        fig.add_trace(go.Scatter(
            x=x,
            y=y,
            mode='markers',
            text=words,
            marker={'size':7, 'color':colors[index]},
            name=document,
            hoverinfo='text',font_family='Roboto'
        ))

    fig.update_layout(
        title='NLP Extracted Topics from Each Document',
        showlegend=True,
        legend={'x':0, 'y':-0.25},
        xaxis={'showline':False, 'zeroline':False,
               'showgrid':False, 'showticklabels':False},
        yaxis={'showline':False, 'zeroline':False,
            'showgrid':False, 'showticklabels':False},font_family='Roboto')
    return [plot(fig, include_plotlyjs=False, output_type='div'), doc_pending]

def populate_nlp_lists(docs):
    '''This method populates the lists
    for the bar graphs'''
    sent = []
    profile_risk = []
    risk = []
    pending = False
    for doc in docs:
        docs_sent, sent_pend = plot_helper.get_doc_sentiment(doc)
        prof_risk, risk_pend = plot_helper.get_profiles_in_doc(doc)
        doc_risk, doc_risk_pend = plot_helper.get_doc_risk(doc)
        sent.extend(docs_sent)
        profile_risk.extend(prof_risk)
        risk.extend(doc_risk)
        if sent_pend or risk_pend or doc_risk_pend:
            pending = True
    return sent, profile_risk, risk, pending

def bar_graph(documents):
    '''Creates a bar plot for
    Avg Risk for Profiles, Messages
    for each document'''
    checked_docs = [doc for doc in documents
            if check_has_messages(doc)]
    doc_names = [doc.display_name for doc in checked_docs]
    sent, profile_risk,risk, pending = populate_nlp_lists(checked_docs)
    if pending:
        return [empty_graph(), pending]

    arrays = [sent, profile_risk, risk]
    trace_names = ['Average Message Sentiment', 'Average Profile Risk',
                   'Average Message Risk']
    traces = []

    for array, name in zip(arrays, trace_names):
        trace = go.Bar(x=doc_names, y=array, name=name,
                       hovertemplate='%{y}')
        traces.append(trace)

    layout = go.Layout(barmode='group',
                       title="Document Sentiment And Risk Ratings",
                       xaxis={'title':'Document Names'},font_family='Roboto')
    fig = go.Figure(data=traces, layout=layout)

    return [plot(fig, include_plotlyjs=False, output_type='div'),pending]

def profile_bar_graph(documents):
    '''Creates a bar graph showing the number
    of messages per document, number of profiles per document,
    and the average number of messages per document'''
    checked_docs = [doc for doc in documents if
                    check_has_messages(doc)]
    doc_names = [doc.display_name for doc in checked_docs]
    docs_message_num = []
    docs_profile_num = []
    docs_avg_message = []
    for doc in checked_docs:
        docs_message_num.extend([plot_helper.get_number_of_messages(doc)])
        docs_profile_num.extend([plot_helper.get_number_of_profiles(doc)])
        docs_avg_message.extend([plot_helper.get_profile_avg_message(doc)])
    arrays = [docs_message_num, docs_profile_num, docs_avg_message]
    trace_names = ['Number of Messages', "Number of Profiles", "Number of Messages per Profile"]
    traces = []
    for array, name in zip(arrays, trace_names):
        traces.append(go.Bar(x=doc_names, y=array, name=name,
                             hovertemplate='%{y}'))

    layout = go.Layout(barmode='group', title='Message Statistics',
                       xaxis={'title':'Document Names'},font_family='Roboto')
    fig = go.Figure(data=traces, layout=layout)

    return [plot(fig, include_plotlyjs=False, output_type='div'),False]

def response_time_dist(documents):
    '''Creates a violin plot
    of message response time for
    each document'''
    time_diff = [plot_helper.doc_time_diff(
        document) for document in documents]
    docs = []
    for index, element in enumerate(time_diff):
        docs.append([documents[index].display_name]
                    *len(element))
    fig = go.Figure()
    colors = plc.n_colors('rgb(5, 200, 200)',
                          'rgb(200, 10, 10)',
                          len(docs) + 1, colortype='rgb')
    for doc,response,color in zip(docs,
                                   time_diff, colors):
        if len(response)>0:
            fig.add_trace(go.Violin(x=response,
                      name=doc[0],
                      line_color=color,
                      box_visible=True,
                      meanline_visible=True))

    fig.update_traces(orientation='h', side='positive',
                      width = 3, points=False, hoverinfo='skip')
    fig.update_layout(
        title="Response Time Distribution",
        xaxis_title="Response Times (Minutes)",
        yaxis={'showline':False, 'zeroline':False,
               'showgrid':False, 'showticklabels':False},
        legend={'x':0, 'y':-0.4},font_family='Roboto')
    return [plot(fig, include_plotlyjs=False, output_type='div'), False]

def all_doc_analysis(doc, messages):
    '''This method returns
    all the graphs relevant for all
    document analysis'''
    bar_description = ("If the sentiment or risk is lower for "
                       "a document than others, it indicates potential "
                       "antisocial behavior in the messages.")
    response_time_description = ("If the distribution is skewed towards "
                                 "lower values, it indicates potential urgency in the "
                                 "conversation")
    risk_dist_description = ("If the distribution of the ridgeplot is skewed"
                             " to the left then it indicates potential antisocial"
                             " behavior in the messages.")
    profile_bar_description = ("If a document has two participants and a lot "
                               "of messages it might indicate that one participant"
                               " is trying to manipulate the other.")
    common_topics_description = ("If documents share the same topic and"
                                 " the same profiles it indicates that the"
                                 " documents are related.")
    return [bar_graph(doc), response_time_dist(doc),
             risk_dist(doc), profile_bar_graph(doc),
            common_topics(messages)], [bar_description,
                                       response_time_description,
                                       risk_dist_description,
                                       profile_bar_description,
                                       common_topics_description]

def check_has_messages(doc):
    '''this method checks if a document
    has associated messages'''
    return Message.objects.filter(source=doc).exists()

def empty_graph():
    '''This method creates an empty Graph'''
    fig = go.Figure()
    return plot(fig, include_plotlyjs=False, output_type='div')

def empty_graph_analysis(num_of_graphs):
    '''This method populates a list of empty
    graphs'''
    return [[empty_graph(),False] for i in range(num_of_graphs)],[
        "" for i in range(num_of_graphs)
    ]

def singular_doc_analysis(messages, doc_nlp):
    '''This method returns all the graphs relevant
    for singular document graphs'''
    sent_and_risk_description = ("If a point on the graph has a low y value"
                                 " it has a negative risk or sentiment which "
                                 "indicates the message contains potential"
                                 " antisocial behavior.")
    wassa_description = ("If the function of a emotion is close to"
                         " 1 there is a high likely hood that emotion"
                         " is present in that message.")
    wassa_ridge_description = ("If the distribution of the emotion is"
                               " skewed to values close to 1 it means "
                               "that emotion is present often in the conversation")
    profile_bar_description = ("If a profile has a low number for risk it means"
                               " the profile has the worst risk and potentially"
                               " conducting antisocial behavior")
    relationship_description = ("If a person is mapped to a topic it "
                                "indicates the spoke about it in a message and shows the "
                                "relation the speaker has to the topic")
    return [[get_graph_risk_and_sentiment(doc_nlp), False],
            [wassa_graphs(doc_nlp), False],
            [wassa_ridgeplot(doc_nlp), False],
            profile_risk_bar_graph(messages),
            relationship_graph(messages)], [sent_and_risk_description,
                                            wassa_description,
                                            wassa_ridge_description,
                                            profile_bar_description,
                                            relationship_description]

def profile_risk_graph(dict_analysis):
    '''Method creates a graph showing the average risk for profiles'''
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=dict_analysis['ID'],
                             y=dict_analysis["Risk"],
                             mode='lines',
                             name=f'{"Risk"} Evaluation'))
    fig.update_layout(title='Risk Scale',
                      xaxis_title='Message Over Time',
                      yaxis_title='Risk Score',
                      paper_bgcolor='rgba(0, 0, 0, 0)',font_family='Roboto')

    return plot(fig, include_plotlyjs=False, output_type='div')

def common_topics(messages):
    '''reate a relationship graph between documents
    and common topics between the documents and the
    profiles that mentioned the topics'''
    doc_dict, has_tasks_pending = plot_helper.get_document_profile_topics(messages)
    topic_dict = plot_helper.change_key_to_topic(doc_dict)
    topic_points = {'text': list(topic_dict.keys())} | get_topic_coords(len(topic_dict.keys()))
    doc_points = {'text': get_documents(topic_dict)} | get_doc_coords(len(
        get_documents(topic_dict)), len(topic_dict.keys()))
    fig = go.Figure()
    for index in range(len(topic_points['text'])):
        fig.add_trace(go.Scatter(x = [topic_points['x'][index]],
                                  y=[topic_points['y'][index]],
                                    text=topic_points['text'][index], **mapping_styles('orange')))
    for index in range(len(doc_points['text'])):
        fig.add_trace(go.Scatter(x=[doc_points['x'][index]],
                                  y = [doc_points['y'][index]],
                                    text =doc_points['text'][index],**mapping_styles('yellow')))

    for topic, doc_owner_pairs in topic_dict.items():
        topic_pos = topic_points['text'].index(topic)
        for doc_owner_pair in doc_owner_pairs:
            doc_pos = doc_points['text'].index(doc_owner_pair[0])
            fig.add_trace(go.Scatter(x=[topic_points['x'][topic_pos],doc_points['x'][doc_pos]],
                                     y=[topic_points['y'][topic_pos],doc_points['y'][doc_pos]],
                                     mode='lines'))
            annotation_x, annotation_y = random_point_between([topic_points['x'][topic_pos],
                                                               topic_points['y'][topic_pos]],
                                                               [doc_points['x'][doc_pos],
                                                                doc_points['y'][doc_pos]])
            fig.add_annotation(x = annotation_x,
                               y = annotation_y,
                               text =doc_owner_pair[1] + " mentioned",
                               showarrow=True,
                               arrowhead=3
                               )
    fig.update_layout(
        title='Common Topics Across Documents',
        showlegend=False,font_family='Roboto',
        xaxis={'visible': False},
        yaxis={'visible': False})
    return [plot(fig, include_plotlyjs=False, output_type='div'), has_tasks_pending]

def random_point_between(point_1, point_2):
    '''Gets a random point along
    the line between the two points provided'''
    random_factor = np.random.uniform(0, 1)
    x = (1 - random_factor) * point_1[0] + random_factor * point_2[0]
    y = (1 - random_factor) * point_1[1] + random_factor * point_2[1]
    return x, y

def get_documents(topic_dict):
    '''Gets the dame of documents
    in the topic_dict structure'''
    documents = set()
    for _, doc_owner_pairs in topic_dict.items():
        for doc_owner_pair in doc_owner_pairs:
            documents.add(doc_owner_pair[0])
    return list(documents)


def get_doc_coords(doc_count, topic_count):
    '''Creates coordinates for the document nodes
    so that the network structure is maintained'''
    left_of_topics = {'x':[]}
    right_of_topics = {'x':[]}
    doc_coords = {}
    for i in range(doc_count):
        if i%2 == 0 or i ==0:
            left_of_topics['x'].append(-1)
        else: right_of_topics['x'].append(1)
    left_of_topics['y'] = get_symmetric_position(len(left_of_topics['x']), topic_count)
    right_of_topics['y'] = get_symmetric_position(len(right_of_topics['x']), topic_count)
    doc_coords['x'] = [item for pair in zip(left_of_topics['x'],
                                            right_of_topics['x']) for item in pair ]
    doc_coords['y'] = [item for pair in zip(left_of_topics['y'],
                                            right_of_topics['y']) for item in pair]

    if len(left_of_topics['x']) > len(right_of_topics['x']):
        doc_coords['x'].append(left_of_topics['x'][-1])
        doc_coords['y'].append(left_of_topics['y'][-1])

    return doc_coords


def get_symmetric_position(doc_count, topic_count):
    '''Gets the symmetric position where
    each data point is the same distance away from
    each other as well as the same distance from the
    last and starting topic nodes'''
    halving_factor = topic_count/(doc_count + 1)
    return [ (i+1) * halving_factor for i in range(doc_count)]

def get_topic_coords(count):
    '''Creates the coordinates for the topic
    nodes'''
    y_axis = 1
    chosen_coordinates = np.array([[0, y_axis]])
    while len(chosen_coordinates) < count:
        y_axis+=1
        coordinates = np.array([0, y_axis])
        min_dists = np.linalg.norm(chosen_coordinates - coordinates, axis=1)
        if np.min(min_dists) >= 1:
            chosen_coordinates = np.append(chosen_coordinates, coordinates[None,:], axis=0)
    return {
        'x': chosen_coordinates[:, 0],
        'y': chosen_coordinates[:, 1]}


def profile_risk_bar_graph(messages):
    '''Creates bar graph showing the average
    risk for every profile in the document'''
    profiles_risk,has_tasks_pending = plot_helper.profiles_risk(messages)
    layout = go.Layout(barmode='group',
                       title='Profile Average Risk Ratings',
                       xaxis={'title':'Profile'},
                       yaxis={'title':'Rating'})
    fig = go.Figure(layout=layout)
    for profile, risks in profiles_risk.items():
        fig.add_trace(go.Bar(x=[profile], y=[np.mean(np.array(risks))],
                             name=profile,
                             showlegend= False, hovertemplate='%{y}'))
    fig.update_layout(font_family='Roboto')
    return [plot(fig,include_plotlyjs=False, output_type='div'), has_tasks_pending]

def profile_risk_gauge(average_risk):
    '''Renders a gauge for the average risk.'''
    fig = go.Figure()
    fig.add_trace(go.Indicator(
        mode='gauge', value=average_risk,
        gauge={
            'shape': 'bullet',
            'axis': {'range': [-1, 1]},
            'steps': [
                {'range': [-1, -0.7],   'color': 'red'},
                {'range': [-0.7, -0.3], 'color': 'orange'},
                {'range': [-0.3, 0.3],  'color': 'yellow'},
                {'range': [0.3, 0.7],   'color': 'lime'},
                {'range': [0.7, 1],     'color': 'green'}],
            'bar': {'color': 'black'}
        }
    ))
    fig.update_layout({
        'paper_bgcolor': 'rgba(0, 0, 0, 0)',
        'plot_bgcolor': 'rgba(0, 0, 0, 0)',
        'height': 80,
        'margin': {'l': 0, 'r': 0, 't': 30, 'b': 30}
    })
    return plot(fig, include_plotlyjs=False, output_type='div')
