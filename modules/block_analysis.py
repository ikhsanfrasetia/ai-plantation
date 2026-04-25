import pandas as pd
from datetime import datetime


def block_productivity(master, produksi, tahun=None):
    """Calculate productivity per block"""
    if tahun is not None:
        produksi_filtered = produksi[produksi["tahun"] == tahun]
    else:
        produksi_filtered = produksi
    
    # Aggregate production by block
    prod = produksi_filtered.groupby(
        ["estate", "afdeling", "blok"]
    )["produksi_tbs_kg"].sum().reset_index()
    
    # Merge with master
    data = pd.merge(master, prod, on=["estate", "afdeling", "blok"], how="left")
    data["produksi_tbs_kg"] = data["produksi_tbs_kg"].fillna(0)
    data["produksi_ton"] = data["produksi_tbs_kg"] / 1000
    data["produktivitas"] = data["produksi_ton"] / data["luas_ha"]
    data["produktivitas"] = data["produktivitas"].fillna(0)
    
    # Calculate age
    current_year = datetime.now().year
    data["umur_tahun"] = current_year - data["tahun_tanam"]
    data["umur_tahun"] = data["umur_tahun"].clip(lower=1)
    
    return data


def worst_blocks(data, n=10):
    """Get n worst performing blocks"""
    return data.sort_values("produktivitas").head(n)


def best_blocks(data, n=10):
    """Get n best performing blocks"""
    return data.sort_values("produktivitas", ascending=False).head(n)


def classify_blocks(data, target=25):
    """Classify blocks based on productivity"""
    result = data.copy()
    result["status"] = result["produktivitas"].apply(
        lambda x: "Optimal" if x >= 22
        else "Underperform" if x >= 17
        else "Critical"
    )
    result["yield_gap"] = (target - result["produktivitas"]).clip(lower=0)
    return result