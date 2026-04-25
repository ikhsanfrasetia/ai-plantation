import streamlit as st
import plotly.express as px


def show_estate_chart(data):
    """Display estate performance chart"""
    fig = px.bar(
        data,
        x="estate",
        y="produksi_ton",
        title="Production by Estate",
        color="estate",
        labels={"produksi_ton": "Production (Ton)", "estate": "Estate"},
        text="produksi_ton"
    )
    fig.update_traces(textposition="outside", texttemplate="%{text:.1f}")
    st.plotly_chart(fig, use_container_width=True)


def show_afdeling_table(data):
    """Display afdeling performance table"""
    st.subheader("📋 Afdeling Performance")
    st.dataframe(data, use_container_width=True)