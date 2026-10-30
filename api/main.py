import sys
from pathlib import Path

import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT / "src"))

from features import load_data
from alerts import compute_alerts
from predict import forecast

app = FastAPI(title="Sales Forecast API")
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])

bundle = joblib.load(ROOT / "models" / "lgbm.pkl")
df = load_data()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/kpis")
def kpis():
    last = df["date"].max()
    cur = df[df["date"] > last - pd.Timedelta(days=30)]
    prev = df[(df["date"] <= last - pd.Timedelta(days=30))
              & (df["date"] > last - pd.Timedelta(days=60))]
    ca_cur, ca_prev = float(cur["sales"].sum()), float(prev["sales"].sum())
    return {
        "date_fin": last.strftime("%Y-%m-%d"),
        "ca_30j": round(ca_cur, 2),
        "ca_30j_precedent": round(ca_prev, 2),
        "variation_pct": round((ca_cur / ca_prev - 1) * 100, 2),
        "top_categorie": cur.groupby("category")["sales"].sum().idxmax(),
        "top_region": cur.groupby("region")["sales"].sum().idxmax(),
    }


@app.get("/alerts")
def alerts():
    return compute_alerts(df)


@app.get("/forecast")
def get_forecast(region: str, category: str, days: int = 7):
    if region not in df["region"].unique() or category not in df["category"].unique():
        raise HTTPException(404, "Région ou catégorie inconnue")
    if not 1 <= days <= 14:
        raise HTTPException(400, "days doit être entre 1 et 14")
    return forecast(bundle["model"], bundle["columns"], df, region, category, days)