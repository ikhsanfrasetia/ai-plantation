import pandas as pd


def estate_summary(master, produksi, tahun=None):
    """Calculate estate summary statistics"""
    total_area = master["luas_ha"].sum()
    
    if tahun is not None:
        produksi_filtered = produksi[produksi["tahun"] == tahun]
    else:
        produksi_filtered = produksi
    
    total_prod = produksi_filtered["produksi_tbs_kg"].sum() / 1000
    
    if total_area > 0:
        productivity = total_prod / total_area
    else:
        productivity = 0
    
    return total_area, total_prod, productivity


def get_estate_production(produksi, tahun=None):
    """Get production by estate"""
    if tahun is not None:
        produksi_filtered = produksi[produksi["tahun"] == tahun]
    else:
        produksi_filtered = produksi
    
    result = produksi_filtered.groupby("estate")["produksi_tbs_kg"].sum().reset_index()
    result["produksi_ton"] = result["produksi_tbs_kg"] / 1000
    
    return result


def get_afdeling_performance(master, produksi, tahun=None):
    """Get performance by afdeling"""
    if tahun is not None:
        produksi_filtered = produksi[produksi["tahun"] == tahun]
    else:
        produksi_filtered = produksi
    
    # Production by afdeling
    prod_afdeling = produksi_filtered.groupby(["estate", "afdeling"])["produksi_tbs_kg"].sum().reset_index()
    prod_afdeling["produksi_ton"] = prod_afdeling["produksi_tbs_kg"] / 1000
    
    # Area by afdeling
    area_afdeling = master.groupby(["estate", "afdeling"])["luas_ha"].sum().reset_index()
    
    # Merge
    result = pd.merge(area_afdeling, prod_afdeling, on=["estate", "afdeling"], how="left")
    result["produksi_ton"] = result["produksi_ton"].fillna(0)
    result["produktivitas"] = result["produksi_ton"] / result["luas_ha"]
    result["produktivitas"] = result["produktivitas"].fillna(0).round(2)
    
    return result