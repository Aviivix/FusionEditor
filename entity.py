import json


class Entity:
    def __init__(self, name):
        with open(file='assets/entities/' + name + '/model_data.json') as j:
            self.model_data = json.load(j)

        with open(file='assets/entities/' + name + '/sheet_data.json') as j:
            self.sheet_data = json.load(j)

        self.model_sheets = []
        for m in self.model_data:
            try:
                for self.model_data[m]['Sheets']:



    def init_model(self, model):
