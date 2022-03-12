
import re
from typing import Any, Dict

def tag_as_dict(tag : str) -> Dict[str, Any]:
    """Split the 'other_tags' column."""
    # Finds and consume all commas between quotes
    # - Avoids splitting values with commas inside quotes.
    if tag is None:
        return {}
    entries = re.split(r"""(?:["]),(?:["]*)""",tag) 
    tag_dict = {}
    for entry in entries:
        # Remove the remaining quotes
        cleaned_entry = entry.replace('"',"")
        key, value = cleaned_entry.split("=>")
        tag_dict[key] = value
    return tag_dict