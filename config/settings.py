"""
Configuration settings for Palm Plantation Analytics
"""

# App Configuration
APP_TITLE = "Palm Plantation Analytics"
APP_ICON = "🌴"
APP_LAYOUT = "wide"

# Production Targets (Ton/Ha)
CRITICAL_MAX = 17
UNDER_MIN = 17
UNDER_MAX = 22
OPTIMAL_MIN = 22

# Default Values
DEFAULT_TARGET = 25
DEFAULT_HARGA = 2300

# Sheet Names
SHEET_MASTER = "MASTER_BLOCK"
SHEET_PRODUKSI = "PRODUKSI_BULANAN"
SHEET_HARGA = "HARGA"
SHEET_PARAMETER = "PARAMETER"

# Column Names
COL_MASTER = ["estate", "afdeling", "blok", "luas_ha", "tahun_tanam", "pokok_ha"]
COL_PRODUKSI = ["estate", "afdeling", "blok", "bulan", "tahun", "produksi_tbs_kg"]