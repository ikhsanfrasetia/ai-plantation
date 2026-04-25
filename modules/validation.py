import pandas as pd
from config.settings import COL_MASTER, COL_PRODUKSI


def validate_columns(master, produksi):
    """Validate required columns in master and produksi sheets"""
    errors = []
    
    for col in COL_MASTER:
        if col not in master.columns:
            errors.append(f"Column '{col}' not found in MASTER_BLOCK")
    
    for col in COL_PRODUKSI:
        if col not in produksi.columns:
            errors.append(f"Column '{col}' not found in PRODUKSI_BULANAN")
    
    if errors:
        raise Exception("\n".join(errors))
    
    if master.empty:
        raise Exception("MASTER_BLOCK sheet is empty")
    
    if produksi.empty:
        raise Exception("PRODUKSI_BULANAN sheet is empty")