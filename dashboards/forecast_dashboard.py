import streamlit as st
import plotly.graph_objects as go


def show_forecast(forecast):
    """Display production forecast"""
    st.subheader("📈 12 Month Production Forecast")
    
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun', 
              'Jul', 'Agu', 'Sep', 'Okt', 'Nov', 'Des']
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=months,
        y=forecast,
        mode="lines+markers",
        name="Forecast",
        line=dict(color="#2ecc71", width=3),
        marker=dict(size=8)
    ))
    
    fig.update_layout(
        xaxis_title="Month",
        yaxis_title="Production (Ton)",
        height=500
    )
    
    st.plotly_chart(fig, use_container_width=True)