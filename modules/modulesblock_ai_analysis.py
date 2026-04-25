import pandas as pd

def detect_problem_blocks(data, harga_tbs, target_yield=25):

    df = data.copy()

    # produktivitas ton/ha
    df["yield_gap"] = target_yield - df["produktifitas"]

    df["yield_gap"] = df["yield_gap"].apply(lambda x: max(x,0))

    # estimasi loss
    df["loss_revenue"] = (
        df["yield_gap"]
        * df["luas_ha"]
        * harga_tbs
        * 1000
    )

    # klasifikasi AI sederhana
    conditions = [
        df["produktifitas"] >= target_yield*0.9,
        df["produktifitas"] >= target_yield*0.7,
        df["produktifitas"] < target_yield*0.7
    ]

    labels = [
        "Normal",
        "Underperform",
        "Critical"
    ]

    df["status"] = pd.cut(
        df["produktifitas"],
        bins=[0, target_yield*0.7, target_yield*0.9, 100],
        labels=["Critical","Underperform","Normal"]
    )

    return df