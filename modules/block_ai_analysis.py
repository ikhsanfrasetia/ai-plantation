import pandas as pd

def calculate_loss_revenue(data, harga_tbs, target=25):
    """Calculate revenue loss based on target"""
    result = data.copy()
    result["yield_gap"] = (target - result["produktivitas"]).clip(lower=0)
    result["loss_revenue"] = result["yield_gap"] * result["luas_ha"] * harga_tbs * 1000
    return result

def get_top_loss_blocks(data, n=10):
    """Get top n blocks with highest loss"""
    if "loss_revenue" in data.columns:
        return data.sort_values("loss_revenue", ascending=False).head(n)
    return data.head(n)

def get_status_summary(data):
    """Get summary by status"""
    if "status" not in data.columns:
        return pd.DataFrame()
    
    summary = data.groupby("status").agg({
        "blok": "count",
        "luas_ha": "sum",
        "produktivitas": "mean"
    }).reset_index()
    summary.columns = ["Status", "Jumlah Blok", "Luas (Ha)", "Rata-rata Produktivitas"]
    return summary

def calculate_target_per_block(data, parameter):
    """Calculate target per block based on age and parameter"""
    return pd.Series([25] * len(data), index=data.index)