import os
import joblib
import pandas as pd
from lightgbm import LGBMRegressor
from features import load_data, add_features, ROOT

data = add_features(load_data())
X = pd.get_dummies(data.drop(columns=["date", "sales", "units", "year"]),
                   columns=["region", "category"], dtype=int)
y = data["sales"]

model = LGBMRegressor(n_estimators=300, learning_rate=0.05, random_state=42, verbose=-1)
model.fit(X, y)

os.makedirs(ROOT / "models", exist_ok=True)
joblib.dump({"model": model, "columns": list(X.columns)}, ROOT / "models" / "lgbm.pkl")
print("Modèle sauvegardé :", X.shape)