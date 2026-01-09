import json
from datetime import datetime
from typing import Any, Optional


class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle datetime objects."""

    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()
        return super().default(o)


def save_to_json(data: Any, output_file: str, indent: Optional[int] = 2):
    """
    Saves data to a JSON file with proper encoding for dates and non-ASCII characters.

    Args:
        data: Data to serialize
        output_file: Path to output file
        indent: JSON indentation (None for compact, default 2)
    """
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=indent,
                  ensure_ascii=False, cls=DateTimeEncoder)
