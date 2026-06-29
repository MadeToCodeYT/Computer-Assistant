import joblib
from extract_entities import extract_from_intent
from intent_router import route
import os

model_path = "intent_model.joblib"

if not os.path.exists(model_path):
    import train_intent_model # This will run the code inside the file, creating the file

model = joblib.load(model_path)

text = "Create a timer for 10 minutes"
intent = model.predict([text])[0]

entities = extract_from_intent(intent, text)
result = route(intent, entities)

print(result)