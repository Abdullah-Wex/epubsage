import json
from datetime import datetime
from typing import Any


class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle datetime objects."""

    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()
        return super().default(o)


def save_to_json(data: Any, output_file: str):
    """
    Saves data to a JSON file with proper encoding for dates and non-ASCII characters.
    """
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False, cls=DateTimeEncoder)
