'''Helper Methods for Quering the database'''
from analyzer.models import Message
from analyzer.io.nlp import wait_nlp_tasks
class Queries():
    '''This class creates queries for
    the django database and allows for
    extendability'''

    def __init__(self):
        '''This method initialises
        the class'''
        self.results = []
        self.pending = False
        self.has_data = True

    def populate_result(self, filter_field, condition):
        '''This method populates the class
        variables'''
        filter_params = {f"{filter_field}": condition}
        messages = Message.objects.filter(
            **filter_params)
        self.results, self.pending = wait_nlp_tasks(messages)

        if self.results is None or None in self.results:
            self.has_data = False

    def get_nlp_data(self, filter_field, conditions, field):
        '''This ,ethod populates a dictionary of
        the NLP results for every message based on
        a filter condition'''
        self.populate_result(filter_field, conditions)
        if self.has_data:
            return [result[field] for result in self.results], self.pending
        return [], self.pending
