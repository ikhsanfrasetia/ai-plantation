import streamlit as st
import plotly.express as px


def show_ai_block_analysis(data):
    """Display AI Block Intelligence dashboard"""
    st.header("🤖 AI Block Intelligence")
    
    # Status distribution
    st.subheader("📊 Block Performance Classification")
    status_count = data["status"].value_counts().reset_index()
    status_count.columns = ["status", "count"]
    
    color_map = {
        "Optimal": "#2ecc71",
        "Underperform": "#f1c40f",
        "Critical": "#e74c3c"
    }
    
    fig = px.pie(
        status_count,
        names="status",
        values="count",
        title="Block Classification Distribution",
        color="status",
        color_discrete_map=color_map,
        hole=0.3
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Top loss blocks
    if "loss_revenue" in data.columns:
        st.subheader("💰 Top Revenue Loss Blocks")
        top_loss = data.sort_values("loss_revenue", ascending=False).head(10)
        display_data = top_loss[["blok", "estate", "afdeling", "produktivitas", "loss_revenue"]].copy()
        display_data["loss_revenue"] = display_data["loss_revenue"].apply(lambda x: f"Rp {x:,.0f}")
        st.dataframe(display_data, use_container_width=True)
        
        # Loss chart
        st.subheader("📉 Revenue Loss Ranking")
        loss_chart = top_loss.sort_values("loss_revenue")
        fig2 = px.bar(
            loss_chart,
            x="loss_revenue",
            y="blok",
            orientation="h",
            title="Top 10 Blocks by Revenue Loss",
            color="status",
            color_discrete_map=color_map
        )
        st.plotly_chart(fig2, use_container_width=True)
    
    # Summary
    st.subheader("📊 AI Insights Summary")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Blocks", len(data))
    with col2:
        st.metric("Average Productivity", f"{data['produktivitas'].mean():.2f} Ton/Ha")
    with col3:
        if "loss_revenue" in data.columns:
            st.metric("Total Loss", f"Rp {data['loss_revenue'].sum():,.0f}")