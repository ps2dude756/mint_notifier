import json
import os

class Source:
    def __init__(self, data_file):
        self.data_file = data_file

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def get_message(self):
        return ''

    def send_message(self, message):
        pass

    def _read_from_file(self, *args):
        with open(self.data_file, 'r') as f:
            data = json.loads(f.read())
            for arg in args:
                data = data[arg]
            return data

    def _write_to_file(self, key, new_data, *args):
        if not os.path.exists(self.data_file):
            with open(self.data_file, 'w') as f:
                f.write(json.dumps({}))
            
        with open(self.data_file, 'r') as f:
            try:
                data = child = json.loads(f.read())
            except ValueError:
                data = child = {}
            for arg in args:
                try:
                    child = child[arg]
                except KeyError:
                    child[arg] = {}
                    child = child[arg]
            child[key] = new_data

        with open(self.data_file, 'w') as f:
            f.write(json.dumps(data))
