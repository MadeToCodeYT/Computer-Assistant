import joblib

model = joblib.load("intent_model.joblib")

text = "remind me"
intent = model.predict([text])[0]

print(intent)