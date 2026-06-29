import re
from datetime import datetime, timedelta

def extract_times(text: str):
    """
    Extracts the hours, minutes, and seconds from the text.
    Args:
        text: The text to extract the time units from.
    Returns:
        A dictionary with the time units.
        {
            "hours": int,
            "minutes": int,
            "seconds": int
        }
    """

    # Match patterns like "2 hours", "10 minutes", "5 seconds"
    pattern = r"(?P<hours>\d+)\s*hours?|\b(?P<minutes>\d+)\s*minutes?|\b(?P<seconds>\d+)\s*seconds?"
    result = {"hours": 0, "minutes": 0, "seconds": 0}

    for match in re.finditer(pattern, text.lower()):
        if match.group("hours"):
            result["hours"] = int(match.group("hours"))
        if match.group("minutes"):
            result["minutes"] = int(match.group("minutes"))
        if match.group("seconds"):
            result["seconds"] = int(match.group("seconds"))

    return result

def extract_date(text: str):
    """
    Extracts the target date from the text.
    Args:
        text: The text to extract the date from.
    Returns:
        A dictionary with the date.
        {
            "date": str
        }
    """
    text = text.lower()
    
    if "today" in text:
        date = datetime.now().strftime("%Y-%m-%d")
    elif "tomorrow" in text:
        date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    else:  # Default to today's date
        date = datetime.now().strftime("%Y-%m-%d")
    
    return {"date": date}

def extract_from_intent(intent: str, text: str):
    """
    Extracts the entities from the text based on the intent.
    Args:
        intent: The intent to extract the entities from.
        text: The text to extract the entities from.
    Returns:
        A dictionary with the entities.
    """
    if intent == "timer":
        return extract_times(text)
    elif intent == "weather":
        return extract_date(text)