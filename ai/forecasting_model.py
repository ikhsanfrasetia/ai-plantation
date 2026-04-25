import pandas as pd
from sklearn.linear_model import LinearRegression


def train_model(produksi):
    """Train linear regression model for forecasting"""
    produksi_bulanan = produksi.groupby(["tahun", "bulan"])["produksi_tbs_kg"].sum().reset_index()
    produksi_bulanan["date"] = pd.to_datetime(
        produksi_bulanan["tahun"].astype(str) + "-" +
        produksi_bulanan["bulan"].astype(str) + "-01"
    )
    produksi_bulanan = produksi_bulanan.sort_values("date")
    produksi_bulanan["t"] = range(len(produksi_bulanan))
    
    X = produksi_bulanan[["t"]]
    y = produksi_bulanan["produksi_tbs_kg"]
    
    model = LinearRegression()
    model.fit(X, y)
    
    return model, produksi_bulanan


def forecast_12_months(model, data):
    """Forecast production for next 12 months"""
    last_t = data["t"].max()
    forecast = []
    
    for i in range(1, 13):
        pred = model.predict([[last_t + i]])
        forecast.append(pred[0] / 1000)
    
    return forecast


def get_forecast_summary(forecast):
    """Get summary statistics of forecast"""
    return {
        "total": sum(forecast),
        "average": sum(forecast) / len(forecast),
        "max": max(forecast),
        "min": min(forecast)
    }