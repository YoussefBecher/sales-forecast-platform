import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load_data():
    df = pd.read_csv(ROOT / "data" / "raw" / "sales.csv", parse_dates=["date"])
    df = df.drop_duplicates()
    df = df.sort_values(["region", "category", "date"]).reset_index(drop=True)
    return df


def add_features(df):
    df = df.copy()

    # Calendrier
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month
    df["dayofweek"] = df["date"].dt.dayofweek
    df["weekofyear"] = df["date"].dt.isocalendar().week.astype(int)
    df["is_weekend"] = (df["dayofweek"] >= 5).astype(int)

    # Historique par région et catégorie
    g = df.groupby(["region", "category"])["sales"]
    for lag in (1, 7, 14, 28):
        df[f"lag_{lag}"] = g.shift(lag)
    for w in (7, 28):
        df[f"roll_mean_{w}"] = g.transform(lambda s: s.shift(1).rolling(w).mean())

    return df.dropna().reset_index(drop=True)


def time_split(df, cutoff="2025-01-01"):
    train = df[df["date"] < cutoff]
    test = df[df["date"] >= cutoff]
    return train, test