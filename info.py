import json


class Info(object):

    @staticmethod
    def load_config(path):
        file = open(path, 'r', encoding='UTF-8')
        data = json.load(file)
        file.close()
        return data
