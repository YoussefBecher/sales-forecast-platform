import pandas as pd


def compute_alerts(df, threshold=0.75, min_days=5):
    df = df.sort_values(["region", "category", "date"]).copy()
    g = df.groupby(["region", "category"])["sales"]
    df["recent7"] = g.transform(lambda s: s.rolling(7).mean())
    df["ref28"] = g.transform(lambda s: s.shift(7).rolling(28).mean())
    df["ratio"] = df["recent7"] / df["ref28"]

    a = df[df["ratio"] < threshold].copy()
    if a.empty:
        return []
    a["new"] = a.groupby(["region", "category"])["date"].diff().dt.days.ne(1)
    a["episode"] = a.groupby(["region", "category"])["new"].cumsum()

    s = (a.groupby(["region", "category", "episode"])
         .agg(debut=("date", "min"), fin=("date", "max"), ratio_min=("ratio", "min"))
         .reset_index().drop(columns="episode"))
    s["jours"] = (s["fin"] - s["debut"]).dt.days + 1
    s = s[s["jours"] >= min_days].copy()
    s["ratio_min"] = s["ratio_min"].round(2)
    s["debut"] = s["debut"].dt.strftime("%Y-%m-%d")
    s["fin"] = s["fin"].dt.strftime("%Y-%m-%d")
    return s.to_dict("records")