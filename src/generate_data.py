import os
import numpy as np
import pandas as pd

rng = np.random.default_rng(42)
dates = pd.date_range("2023-01-01", "2025-12-31", freq="D")
regions = ["Tunis", "Sfax", "Sousse", "Nabeul"]
categories = {"Électronique": 120, "Mobilier": 80, "Vêtements": 50, "Alimentaire": 25}

rows = []
for region in regions:
    reg_factor = rng.uniform(0.8, 1.3)
    for cat, base in categories.items():
        t = np.arange(len(dates))
        trend = 1 + 0.0004 * t
        season = 1 + 0.25 * np.sin(2 * np.pi * t / 365.25) + 0.10 * np.sin(2 * np.pi * t / 7)
        promo = np.where(rng.random(len(dates)) < 0.05, 1.4, 1.0)
        noise = rng.normal(1, 0.08, len(dates))
        units = np.maximum(0, base * reg_factor * trend * season * promo * noise / 10).round()
        price = base * rng.uniform(0.95, 1.05, len(dates))
        sales = (units * price).round(2)

        # baisse simulée (utile pour la détection d'anomalies)
        drop = (dates >= "2025-06-01") & (dates <= "2025-06-20") & (region == "Sfax") & (cat == "Mobilier")
        sales = np.where(drop, sales * 0.5, sales)

        rows.append(pd.DataFrame({
            "date": dates,
            "region": region,
            "category": cat,
            "units": units,
            "sales": sales,
        }))

df = pd.concat(rows, ignore_index=True)

os.makedirs("data/raw", exist_ok=True)
df.to_csv("data/raw/sales.csv", index=False)

print(df.shape)
print(df.head())