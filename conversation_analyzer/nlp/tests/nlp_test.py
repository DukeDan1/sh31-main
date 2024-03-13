'''This file is testing for NLP'''

import pandas as pd
from flair.data import Sentence
from flair.nn import Classifier
from flair.embeddings import TransformerDocumentEmbeddings
import flair.datasets
from flair.data import Corpus
from flair.models import  TextRegressor
from flair.trainers import ModelTrainer

#test of pre-trained models by Flair,
#test of Flair trained on other datasets to come...

def main():
    '''main method to run nlp models'''
    conversation = pd.read_csv("conversation_analyzer/nlp/tests/temp.csv")
    ner_large(conversation)
    ner_onto_large(conversation)
    sentiment(conversation)
    ner_66_class(conversation)
    create_corpus()
    test_corpus(conversation)

def create_corpus():
    '''Method that trains Wassa Regressors'''
    joy = flair.datasets.WASSA_JOY()
    corpus : Corpus = joy
    corpus.make_label_dictionary(label_type='class', add_unk=True)
    doc_embed = TransformerDocumentEmbeddings('distilbert-base-uncased', fine_tune = True)
    classifiar = TextRegressor(document_embeddings=doc_embed,  label_name='class')
    trainer = ModelTrainer(classifiar, corpus)

    trainer.fine_tune('resources/taggers/wassa/joy',
                  learning_rate=5.0e-5,
                  mini_batch_size=4,
                  max_epochs=10,
                  )

def test_corpus(conversation):
    '''Method outputs result of a Wassa Regressor for testing purposes'''
    with open("joy.txt", 'a', encoding='utf-8') as file:
        tagger = TextRegressor.load('resources/taggers/wassa/joy/final-model.pt')
        sen = conversation['message']

        for i in sen:
            sin = Sentence(i)
            tagger.predict(sin)
            file.write(str(sin) + "\n")
    file.close()

def ner_large(conversation):
    ''' NER classifion model with largest dataset'''
    with open("ner_large.txt", 'a', encoding='utf-8') as file:
        tagger = Classifier.load('ner-large')
        sen = conversation['message']

        for i in sen:
            sin = Sentence(i)
            tagger.predict(sin)
            file.write(str(sin) + "\n")
    file.close()

def ner_66_class(conversation):
    ''' NER classifion model with largest label dataset'''
    with open("ner_66.txt", 'a',encoding='utf-8') as file:
        tagger = Classifier.load('FEWNERD')
        sen = conversation['messages']
        for i in sen:
            sin = Sentence(i)
            tagger.predict(sin)
            file.write(str(sin) + "\n")
        file.close()

def ner_onto_large(conversation):
    '''NER classification with 18 classifictions model'''
    with open("ner_onto_large.txt", 'a', encoding='utf-8') as file:
        tagger = Classifier.load('ner-ontonotes-large')
        sen = conversation['message']

        for i in sen:
            sin = Sentence(i)
            tagger.predict(sin)
            file.write(str(sin) + "\n")
    file.close()

def sentiment(conversation):#
    '''Sentiment classifiction'''
    with open("sentiment.txt", 'a', encoding='utf-8') as file:
        tagger = Classifier.load('sentiment')
        sen = conversation['message']

        for i in sen:
            sin = Sentence(i)
            tagger.predict(sin)
            file.write(str(sin) + "\n")
    file.close()
    #add trained sentiment on emotion extreme datasets


if __name__ == '__main__':
    main()
