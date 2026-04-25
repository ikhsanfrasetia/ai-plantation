import streamlit as st


def show_kpi(area, prod, productivity, loss):
    """Display executive KPI dashboard"""
    st.header("📊 Executive Dashboard")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Area (Ha)", f"{area:,.2f}")
    
    with col2:
        st.metric("Total Production (Ton)", f"{prod:,.2f}")
    
    with col3:
        st.metric("Productivity (Ton/Ha)", f"{productivity:.2f}")
    
    with col4:
        st.metric("Estimated Loss (Rp)", f"Rp {loss:,.0f}")