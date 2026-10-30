import pandas as pd


def forecast(model, cols, df, region, category, days=7):
    hist = (df[(df["region"] == region) & (df["category"] == category)]
            .sort_values("date")[["date", "sales"]].copy())
    out = []
    for _ in range(days):
        s = hist["sales"]
        d = hist["date"].max() + pd.Timedelta(days=1)
        row = {
            "month": d.month,
            "dayofweek": d.dayofweek,
            "weekofyear": int(d.isocalendar().week),
            "is_weekend": int(d.dayofweek >= 5),
            "lag_1": s.iloc[-1], "lag_7": s.iloc[-7],
            "lag_14": s.iloc[-14], "lag_28": s.iloc[-28],
            "roll_mean_7": s.iloc[-7:].mean(),
            "roll_mean_28": s.iloc[-28:].mean(),
            "region": region, "category": category,
        }
        X = pd.get_dummies(pd.DataFrame([row]), columns=["region", "category"], dtype=int)
        X = X.reindex(columns=cols, fill_value=0)
        pred = float(model.predict(X)[0])
        out.append({"date": d.strftime("%Y-%m-%d"), "forecast": round(pred, 2)})
        hist = pd.concat([hist, pd.DataFrame({"date": [d], "sales": [pred]})],
                         ignore_index=True)
    return out