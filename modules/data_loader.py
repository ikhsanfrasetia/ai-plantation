import pandas as pd
from config.settings import SHEET_MASTER, SHEET_PRODUKSI, SHEET_HARGA, SHEET_PARAMETER


def load_excel(file):
    """Load all sheets from Excel file"""
    master = pd.read_excel(file, sheet_name=SHEET_MASTER)
    produksi = pd.read_excel(file, sheet_name=SHEET_PRODUKSI)
    harga = pd.read_excel(file, sheet_name=SHEET_HARGA)
    
    # Try to load parameter sheet (optional)
    try:
        parameter = pd.read_excel(file, sheet_name=SHEET_PARAMETER)
        print("Parameter sheet loaded successfully")
    except:
        # Create default parameter if sheet doesn't exist
        parameter = pd.DataFrame({
            'umur_min': [3, 6, 11, 16, 21],
            'umur_max': [5, 10, 15, 20, 25],
            'potensi_ton_ha': [15, 24, 28, 22, 18]
        })
        print("Using default parameter values (sheet not found)")
    
    # Clean column names
    master.columns = master.columns.str.strip()
    produksi.columns = produksi.columns.str.strip()
    harga.columns = harga.columns.str.strip()
    if parameter is not None:
        parameter.columns = parameter.columns.str.strip()
    
    return master, produksi, harga, parameter