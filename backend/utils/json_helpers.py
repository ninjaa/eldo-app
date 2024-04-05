import re
import json
from bson import ObjectId
from datetime import datetime


class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        elif isinstance(o, datetime):
            return o.isoformat()
        return super().default(o)


def clean_json(data):
    if isinstance(data, list):
        return [clean_json(item) for item in data]
    elif isinstance(data, dict):
        return {key: clean_json(value) for key, value in data.items()}
    elif isinstance(data, ObjectId):
        return str(data)
    elif isinstance(data, datetime):
        return data.isoformat()
    else:
        return data


def extract_json(response):
    json_start = response.index("{")
    json_end = response.rfind("}")
    json_string = response[json_start:json_end + 1]

    # Remove newline characters from the JSON string
    json_string = json_string.replace("\n", "")

    # Escape special characters using a single regular expression
    json_string = re.sub(r'\\(?!["\\\/bfnrt])', r'\\\\', json_string)

    return json.loads(json_string)
