import json

def read_json(file_path, key):
    try:
        with open(file_path, 'r') as json_file:
            data = json.load(json_file)
            return data.get(key)
    except FileNotFoundError:
        return None
