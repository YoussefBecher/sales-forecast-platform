import sys
from pathlib import Path

import joblib
import pandas as pd

sys.path.append(str(Path(__file__).resolve().parent))
from features import load_data, ROOT
from alerts import compute_alerts
from predict import forecast

df = load_data()
bundle = joblib.load(ROOT / "models" / "lgbm.pkl")

out = ROOT / "data" / "bi"
out.mkdir(parents=True, exist_ok=True)

# 1. Historique des ventes
df.to_csv(out / "sales.csv", index=False)

# 2. Prévisions à 14 jours pour chaque région et catégorie
rows = []
for region, category in df[["region", "category"]].drop_duplicates().itertuples(index=False):
    for f in forecast(bundle["model"], bundle["columns"], df, region, category, 14):
        rows.append({"region": region, "category": category, **f})
pd.DataFrame(rows).to_csv(out / "forecast.csv", index=False)

# 3. Alertes de baisse
pd.DataFrame(compute_alerts(df)).to_csv(out / "alerts.csv", index=False)

print("Export terminé :", [p.name for p in out.iterdir()])