import streamlit as st
import pandas as pd


def show_block_table(data, title="Block Performance"):
    """Display block data table"""
    st.subheader(title)
    
    if data.empty:
        st.info("No data available")
        return
    
    # Select columns to display
    display_cols = ["estate", "afdeling", "blok", "luas_ha", "produktivitas", "umur_tahun"]
    available_cols = [col for col in display_cols if col in data.columns]
    
    display_data = data[available_cols].copy()
    
    if "produktivitas" in display_data.columns:
        display_data["produktivitas"] = display_data["produktivitas"].round(2)
    
    st.dataframe(display_data, use_container_width=True)