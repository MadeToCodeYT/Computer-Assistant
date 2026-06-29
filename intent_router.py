def timer(hours:int, minutes:int, seconds:int):
    return f"Calling timer('{hours}hr', '{minutes}min', '{seconds}sec')"

def weather(date:str):
    return f"Calling weather('{date}')"

def route(intent, data:dict[str, int|str]):
    if intent == "timer":
        return timer(data["hours"], data["minutes"], data["seconds"])
    elif intent == "weather":
        return weather(data["date"])
    else:
        raise NotImplementedError(f"Unknown intent: {intent}")