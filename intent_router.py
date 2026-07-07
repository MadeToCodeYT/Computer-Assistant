import subprocess

def timer(hours:int, minutes:int, seconds:int):
    units = []
    if hours:
        units.append(f"{hours}hr")
    if minutes:
        units.append(f"{minutes}min")
    if seconds:
        units.append(f"{seconds}sec")
    if units:
        if len(units) == 1:
            return f"Setting a timer for {units[0]}"
        elif len(units) == 2:
            return f"Setting a timer for {units[0]} and {units[1]}"
        else:
            return f"Setting a timer for {', '.join(units[:-1])}, and {units[-1]}"
   
    else:
        return "A duration is required to set a timer."

def weather(date: str, wind_speed:int, temperature_high:int, temperature_low:int, rain_chance:int):
    if rain_chance < 10:
        return f"{date}'s a sunny day with a high of {temperature_high}°F and a low of {temperature_low}°F. The wind speed is {wind_speed}."
    elif rain_chance < 30:
        return f"{date}'s a cloudy day with a high of {temperature_high}°F and a low of {temperature_low}°F. The wind speed is {wind_speed}. There's around a {rain_chance}% chance of rain."
    else:
        return f"{date}'s a rainy day with a high of {temperature_high}°F and a low of {temperature_low}°F. The wind speed is {wind_speed}. There's around a {rain_chance}% chance of rain."

def volume(type: str, percentage: int):
    if percentage == -1:
        return "I couldn't get the volume, please try again."
    
    targetPercent = 0
    if type == "unmute":
        targetPercent = 10
    elif type == "mute":
        targetPercent = 0
    elif type in ["increase", "set"]:
        targetPercent = percentage
    elif type == "decrease":
        targetPercent = -1*percentage

    try:
        output = subprocess.check_output(
            ["osascript", "-e", "output volume of (get volume settings)"],
            text=True
        )
        newVolume = int(output.strip())
    except Exception as e:
        print(f"Error getting volume: {e}")
        return None

    if type in ["set", "unmute", "mute"]:
        newVolume = targetPercent
    else:
        newVolume += targetPercent

    try:
        subprocess.check_call([
            "osascript", "-e", f"set volume output volume {max(0, min(100, newVolume))}"
        ])
        return f"The volume has been set to {newVolume}%."
    except Exception as e:
        print(f"Error setting volume: {e}")

def openapp(appName: str):
    try:
        subprocess.check_call(["open", "-a", appName])
        return f"Opening {appName}..."
    except Exception:
        return f"Unable to find application named '{appName}'."
   
def closeapp(appName: str):
    try:
        script = f'tell application "{appName}" to quit'
        subprocess.check_call(["osascript", "-e", script])
        return f"Closing {appName}..."
    except Exception:
        return f"Unable to find or close application named '{appName}'."

def route(intent, data:dict[str, int|str]):
    if intent == "timer":
        return timer(data["hours"], data["minutes"], data["seconds"])
    elif intent == "weather":
        return weather(data["date"].capitalize(), data["wind_speed"], data["temperature_high"], data["temperature_low"], data["rain_chance"])
    elif intent == "volume":
        return volume(data["volumeType"], data["volume"])
    elif intent == "openapp":
        return openapp(data["appName"])
    elif intent == "closeapp":
        return closeapp(data["appName"])
    else:
        raise NotImplementedError(f"Unknown intent: {intent}")