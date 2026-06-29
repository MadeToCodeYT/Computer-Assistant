import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

df = pd.read_csv("data/intents.csv")

X_train, X_test, y_train, y_test = train_test_split(
    df["text"], df["intent"], test_size=0.2, random_state=42
)

model = make_pipeline(
    TfidfVectorizer(),
    LogisticRegression(max_iter=1000)
)

model.fit(X_train, y_train)

joblib.dump(model, "intent_model.joblib")

if __name__ == "__main__":
    print(f"Accuracy: {100*model.score(X_test, y_test):.0f}%")
    print("Saved model to intent_model.joblib")