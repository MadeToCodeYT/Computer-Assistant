# Computer Assistant

| File Name | Purpose |
| --- | --- |
| `intents.csv` | Stores examples with intents |
| `extract_entities.py` | Extracts specfic data from text |
| `intent_router.py` | Uses intent and data to call a specific function |
| `train_intent_model.py` | Creates a model which learns from `intents.csv` |
| `app.py` | Entry point for user input, uses model to predict, then routes the output to a function |