import streamlit as st
import plotly.express as px
import pandas as pd

from modules.data_loader import load_excel
from modules.validation import validate_columns
from modules.estate_analysis import estate_summary
from modules.block_analysis import block_productivity, worst_blocks, best_blocks, classify_blocks
from modules.heatmap import prepare_heatmap
from modules.block_ai_analysis import calculate_loss_revenue, get_top_loss_blocks

from dashboards.executive_dashboard import show_kpi
from dashboards.block_dashboard import show_block_table
from dashboards.heatmap_dashboard import show_heatmap
from dashboards.forecast_dashboard import show_forecast
from dashboards.block_ai_dashboard import show_ai_block_analysis

from ai.forecasting_model import train_model, forecast_12_months, get_forecast_summary

from config.settings import APP_TITLE, APP_ICON, APP_LAYOUT


# =============================
# PAGE CONFIG
# =============================
st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout=APP_LAYOUT
)


# =============================
# SIDEBAR
# =============================
st.sidebar.title(f"{APP_ICON} {APP_TITLE}")

menu = st.sidebar.radio(
    "Navigation",
    [
        "Executive Dashboard",
        "Estate Analysis",
        "Block Analysis",
        "AI Block Intelligence",
        "Productivity Heatmap",
        "Production Forecast"
    ]
)

st.sidebar.markdown("---")

# Year filter
st.sidebar.subheader("📅 Filter")
tahun_options = ["Semua Tahun"]
tahun_terpilih = st.sidebar.selectbox("Pilih Tahun Analisis", tahun_options)

st.sidebar.markdown("---")

# File uploader
file = st.sidebar.file_uploader(
    "📂 Upload Plantation Data",
    type=["xlsx"],
    help="Upload Excel file with sheets: MASTER_BLOCK, PRODUKSI_BULANAN, HARGA, PARAMETER"
)


# =============================
# HEADER
# =============================
st.title(f"{APP_ICON} {APP_TITLE}")
st.caption("Enterprise Analytics System for Palm Plantation Management")


# =============================
# MAIN APP
# =============================
if file is None:
    st.info("📁 Upload Excel file in sidebar to start analysis")
    
    with st.expander("📋 Required Excel Structure"):
        st.markdown("""
        **Sheet MASTER_BLOCK:**
        - estate, afdeling, blok, luas_ha, tahun_tanam, pokok_ha
        
        **Sheet PRODUKSI_BULANAN:**
        - estate, afdeling, blok, bulan, tahun, produksi_tbs_kg
        
        **Sheet HARGA:**
        - tahun, harga_tbs
        
        **Sheet PARAMETER:**
        - umur_min, umur_max, potensi_ton_ha
        """)

else:
    try:
        # =============================
        # LOAD DATA
        # =============================
        with st.spinner("Loading data..."):
            master, produksi, harga, parameter = load_excel(file)
            validate_columns(master, produksi)
        
        st.success("✅ Data loaded successfully!")
        
        # Update year options
        tahun_list = sorted(produksi["tahun"].unique())
        tahun_options = ["Semua Tahun"] + [int(t) for t in tahun_list]
        tahun_terpilih = st.sidebar.selectbox("Pilih Tahun Analisis", tahun_options, key="tahun_select")
        
        # Filter year
        if tahun_terpilih == "Semua Tahun":
            tahun_filter = None
        else:
            tahun_filter = int(tahun_terpilih)
        
        # Get price
        if tahun_filter:
            harga_row = harga[harga["tahun"] == tahun_filter]
            if not harga_row.empty:
                harga_tbs = harga_row["harga_tbs"].iloc[0]
            else:
                harga_tbs = harga["harga_tbs"].iloc[0]
        else:
            harga_tbs = harga["harga_tbs"].iloc[0]
        
        # =============================
        # EXECUTIVE DASHBOARD
        # =============================
        if menu == "Executive Dashboard":
            area, prod, productivity = estate_summary(master, produksi, tahun_filter)
            target = 25
            loss = (target - productivity) * area * harga_tbs * 1000
            loss = max(0, loss)
            show_kpi(area, prod, productivity, loss)
        
        # =============================
        # ESTATE ANALYSIS
        # =============================
        elif menu == "Estate Analysis":
            st.header("🏢 Estate Production Performance")
            
            # Filter tahun
            if tahun_filter:
                produksi_filtered = produksi[produksi["tahun"] == tahun_filter]
            else:
                produksi_filtered = produksi
            
            # Chart by estate
            estate_data = produksi_filtered.groupby("estate")["produksi_tbs_kg"].sum().reset_index()
            estate_data["produksi_ton"] = estate_data["produksi_tbs_kg"] / 1000
            
            fig = px.bar(
                estate_data,
                x="estate",
                y="produksi_ton",
                title="Production by Estate",
                color="estate",
                labels={"produksi_ton": "Production (Ton)", "estate": "Estate"}
            )
            fig.update_traces(textposition="outside", texttemplate="%{y:.1f}")
            st.plotly_chart(fig, use_container_width=True)
            
            # Table by afdeling
            st.subheader("📋 Afdeling Performance")
            
            prod_afdeling = produksi_filtered.groupby(["estate", "afdeling"])["produksi_tbs_kg"].sum().reset_index()
            prod_afdeling["produksi_ton"] = prod_afdeling["produksi_tbs_kg"] / 1000
            
            area_afdeling = master.groupby(["estate", "afdeling"])["luas_ha"].sum().reset_index()
            
            afdeling_data = pd.merge(area_afdeling, prod_afdeling, on=["estate", "afdeling"], how="left")
            afdeling_data["produksi_ton"] = afdeling_data["produksi_ton"].fillna(0)
            afdeling_data["produktivitas"] = (afdeling_data["produksi_ton"] / afdeling_data["luas_ha"]).round(2)
            
            st.dataframe(afdeling_data, use_container_width=True)
        
        # =============================
        # BLOCK ANALYSIS
        # =============================
        elif menu == "Block Analysis":
            data = block_productivity(master, produksi, tahun_filter)
            
            col1, col2 = st.columns(2)
            with col1:
                worst = worst_blocks(data, 10)
                show_block_table(worst, "🔴 Top 10 Worst Performing Blocks")
            with col2:
                best = best_blocks(data, 10)
                show_block_table(best, "🟢 Top 10 Best Performing Blocks")
        
        # =============================
        # AI BLOCK INTELLIGENCE
        # =============================
        elif menu == "AI Block Intelligence":
            data = block_productivity(master, produksi, tahun_filter)
            data = classify_blocks(data)
            
            # Ensure status column exists
            if "status" not in data.columns:
                data["status"] = data["produktivitas"].apply(
                    lambda x: "Optimal" if x >= 22 else "Underperform" if x >= 17 else "Critical"
                )
            
            data = calculate_loss_revenue(data, harga_tbs)
            show_ai_block_analysis(data)
        
        # =============================
        # PRODUCTIVITY HEATMAP
        # =============================
        elif menu == "Productivity Heatmap":
            data = block_productivity(master, produksi, tahun_filter)
            heatmap_data = prepare_heatmap(data)
            show_heatmap(
                data=None,
                param_df=parameter,
                master_df=master,
                produksi_df=data
            )
        
        # =============================
        # PRODUCTION FORECAST
        # =============================
        elif menu == "Production Forecast":
            model, prod_data = train_model(produksi)
            forecast = forecast_12_months(model, prod_data)
            show_forecast(forecast)
            
            summary = get_forecast_summary(forecast)
            st.subheader("📊 Forecast Summary")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total (12 Months)", f"{summary['total']:.0f} Ton")
            with col2:
                st.metric("Average Monthly", f"{summary['average']:.0f} Ton")
            with col3:
                st.metric("Peak Month", f"{summary['max']:.0f} Ton")
    
    except Exception as e:
        st.error("❌ Error processing data")
        st.exception(e)
        st.info("💡 Make sure Excel file structure matches the required template")