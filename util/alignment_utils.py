import json
import os

def load_gazetteer_from_json(path_,gazetteer_type):

    filepath = os.path.join(path_,gazetteer_type)
    with open(filepath) as json_file:
        data = json.load(json_file)
    return data

def load_gazetteer_from_txt(path_,gazetteer_type):
    filepath = os.path.join(path_, gazetteer_type)

    with open(filepath,'r') as file:
        data = file.readlines()
    return data