import re
import requests
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

def extract_weather(text: str):
    """
    Extracts the weather data from the text. Temperatures will be in Fahrenheit and speed will be in miles per hour.
    Args:
        text: The text to extract the weather data from.
    Returns:
        A dictionary with the weather data.
        {
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
        "wind_speed": wind_speed,
        "temperature_high": temperature_high,
        "temperature_low": temperature_low,
        "rain_chance": rain_chance
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