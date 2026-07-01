import re
import requests

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

def extract_weather(text: str):
    """
    Extracts the weather data from the text. Temperatures will be in Fahrenheit and speed will be in miles per hour.
    Args:
        text: The text to extract the weather data from.
    Returns:
        A dictionary with the weather data.
        {
            "date": str,
            "wind_speed": int,
            "temperature_high": int,
            "temperature_low": int,
            "rain_chance": int,
        }
    """
    def get_latitude_longitude():
        ip_info = requests.get("https://ipinfo.io/json", timeout=10).json()
        if "loc" in ip_info:
            lat_str, lon_str = ip_info["loc"].split(",")
            return float(lat_str), float(lon_str)
        else:
            raise Exception("Could not determine location from IP.")
    

    # Find which date to use
    text = text.lower()

    if "today" in text:
        dates = "today"
    elif "tomorrow" in text:
        dates = "tomorrow"
    # elif "week" in text:
    #     dates = "week"
    else:  # Default to today's date
        dates = "today"

    # Get weather data based on location
    lat, lon = get_latitude_longitude()
    headers = {
        "Accept": "application/geo+json"
    }
    points_url = f"https://api.weather.gov/points/{lat},{lon}"
    points = requests.get(points_url, headers=headers, timeout=20).json()
    forecast_url = points["properties"]["forecast"]
    daily = requests.get(forecast_url, headers=headers, timeout=20).json()["properties"]["periods"]
    temperature_highs = [p["temperature"] for p in daily if p["isDaytime"]]
    temperature_lows = [p["temperature"] for p in daily if not p["isDaytime"]]
    wind_speeds = [p["windSpeed"] for p in daily]
    rain_chances = [p["probabilityOfPrecipitation"]["value"] for p in daily]

    if dates == "today":
        temperature_high = temperature_highs[0]
        temperature_low = temperature_lows[0]
        wind_speed = wind_speeds[0]
        rain_chance = rain_chances[0]
    elif dates == "tomorrow":
        temperature_high = temperature_highs[1]
        temperature_low = temperature_lows[1]
        wind_speed = wind_speeds[1]
        rain_chance = rain_chances[1]
    return {
        "date": dates,
        "wind_speed": wind_speed,
        "temperature_high": temperature_high,
        "temperature_low": temperature_low,
        "rain_chance": rain_chance
    }

def extract_volume_details(text: str):
    """
    Extracts the volume percentage needed to set/change by.
    Args:
        text: The text to extract the volume details from.
    Returns:
        A dictionary with the volume details.
        {
            "volumeType": str,
            "volume": int,
        }
    """

def extract_volume_details(text: str):
    """
    Extracts the volume percentage needed to set/change by.
    Args:
        text: The text to extract the volume details from.
    Returns:
        A dictionary with the volume details.
        {
            "volumeType": str,
            "volume": int,
        }
    """
    
    text = text.lower()

    match = re.search(r'(\d{1,3})\s*%', text)
    if match:
        percentage = int(match.group(1))
    else:
        percentage = -1

    if any(word in text for word in ["decrease", "lower", "reduce"]):
        volume_type = "decrease"
    elif any(word in text for word in ["increase", "raise"]):
        volume_type = "increase"
    elif any(word in text for word in ["set", "put"]):
        volume_type = "set"
    elif "unmute" in text:
        volume_type = "unmute"
    elif "mute" in text:
        volume_type = "mute"
    else:
        volume_type = ""

    return {
        "volumeType": volume_type,
        "volume": percentage
    }

def extract_app_name(text: str):
    """
    Extracts the app name to open/close.
    Args:
        text: The text to extract the app name from.
    Returns:
        A dictionary with the app name.
        {
            "appName": str
        }
    """

    # Remove common phrases that aren't part of the app name
    unnecessary_words = [
        "open", "start", "launch", "close", "quit", "please", "can", "you", "the", "app", "application", "my"
    ]
    text = text.lower()
    text = text.replace("?", "").replace(".", "").replace(",", "")
    words = text.split()
    filtered = [word for word in words if word not in unnecessary_words]
    newText = " ".join(filtered)
    app_name = " ".join([word.capitalize() for word in newText.split()])
    
    return {
        "appName": app_name
    }

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
        return extract_weather(text)
    elif intent == "volume":
        return extract_volume_details(text)
    elif intent == "openapp":
        return extract_app_name(text)
    elif intent == "closeapp":
        return extract_app_name(text)
    else:
        raise NotImplementedError(intent, text)