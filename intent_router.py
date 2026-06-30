def timer(hours:int, minutes:int, seconds:int):
    return f"Calling timer('{hours}hr', '{minutes}min', '{seconds}sec')"

def weather(wind_speed:int, temperature_high:int, temperature_low:int, rain_chance:int):
    if rain_chance < 10:
        return f"It's a sunny day with a high of {temperature_high}°F and a low of {temperature_low}°F. The wind speed is {wind_speed}."
    elif rain_chance < 30:
        return f"It's a cloudy day with a high of {temperature_high}°F and a low of {temperature_low}°F. The wind speed is {wind_speed}. There's around a {rain_chance}% chance of rain."
    else:
        return f"It's a rainy day with a high of {temperature_high}°F and a low of {temperature_low}°F. The wind speed is {wind_speed}. There's around a {rain_chance}% chance of rain."

def route(intent, data:dict[str, int|str]):
    if intent == "timer":
        return timer(data["hours"], data["minutes"], data["seconds"])
    elif intent == "weather":
        return weather(data["wind_speed"], data["temperature_high"], data["temperature_low"], data["rain_chance"])
    else:
        raise NotImplementedError(f"Unknown intent: {intent}")