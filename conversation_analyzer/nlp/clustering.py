'''Kmeans clustering'''

from collections import defaultdict
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder
from conversation_analyzer.settings import BASE_DIR

def k_cluster(nlp_results):
    '''This method is the main method
    which calls the helper methods for
    K_means cluster Graph
    to be produced'''
    if len(nlp_results) == 0:
        return None

    word_risk_tuple_dict = defaultdict(lambda: [0, 0])
    for nlp_result in nlp_results:
        risk = nlp_result['risk']
        for useful_word in nlp_result['useful_words']:
            word_risk_tuple_dict[useful_word][0] += risk
            word_risk_tuple_dict[useful_word][1] += 1

    risk_word_pairs = [(risk_tuple[0] / risk_tuple[1], word)
        for word, risk_tuple in word_risk_tuple_dict.items()]

    labels, vectors = get_vector(risk_word_pairs)
    return cluster_pipeline(labels, vectors)

def get_vector(data):
    '''This method gets the glove2word vectors
    for each word in the list and removes words that
    are not contained in the glove2word'''
    word_vectors = np.load(f'{BASE_DIR}/nlp/glove_vecs.npz')
    word_vecs, words = word_vectors['word_vecs'], word_vectors['words']
    contained_words = []
    def first_word_contained(data):
        index = 0
        while not data[index][1] in words:
            index += 1
        return index
    index_of_first_word = first_word_contained(data)
    vectors = word_vecs[words.searchsorted(data[index_of_first_word][1])].reshape((1, 300))
    contained_words.append(data[index_of_first_word])

    for word in data[index_of_first_word:]:
        if word[1] in words:
            vec = word_vecs[words.searchsorted(word[1])].reshape((1, 300))
            vectors = np.append(vectors, vec, axis=0)
            contained_words.append(word)

    return contained_words, vectors

def cluster_pipeline(true_labels_names, data):
    '''This method creates the Pipeline for
    the K_Means clustering algorithm
    and produces the graph'''
    isolated_risk = np.array([word[0] for word in true_labels_names]).reshape(-1,1)
    isolated_word = [word[1] for word in true_labels_names]

    label_encoder = LabelEncoder()
    true_labels = label_encoder.fit_transform(isolated_word)

    pca = PCA(n_components=1, random_state=42)
    pca_result = pca.fit_transform(data)

    result = np.hstack((pca_result, isolated_risk))
    clusterer = Pipeline([(
        "kmeans",
        KMeans(
            n_clusters=10,
            init="k-means++",
            n_init=50,
            max_iter=500,
            random_state=42,
        )
    )])
    pipe = Pipeline([
        ("clusterer", clusterer)
    ])
    pipe.fit(result)

    pcadf = pd.DataFrame(
        result,
        columns=["Vector", "Risk"],
    )

    if hasattr(pipe["clusterer"]["kmeans"], 'labels_'):
        # Access the labels_ attribute here
        predicted_labels = pipe["clusterer"]["kmeans"].labels_
    else:
        predicted_labels = []

    pcadf["predicted_cluster"] = predicted_labels
    pcadf["true_label"] = label_encoder.inverse_transform(true_labels)
    return pcadf
