import streamlit as st
import plotly.express as px
import pandas as pd


def show_heatmap(data, param_df=None, master_df=None):
    """
    Menampilkan productivity heatmap dengan fitur lengkap
    """
    
    # =============================
    # KONFIGURASI
    # =============================
    CRITICAL_MAX = 17
    OPTIMAL_MIN = 22
    
    # Buat status column
    data["status"] = data["produktivitas"].apply(
        lambda x: "Optimal" if x >= OPTIMAL_MIN
        else "Underperform" if x >= CRITICAL_MAX
        else "Critical"
    )
    
    # =============================
    # SIDEBAR FILTERS
    # =============================
    st.sidebar.markdown("---")
    st.sidebar.subheader("🎯 Heatmap Filters")
    
    # Filter Estate
    estate_list = ["Semua Estate"] + sorted(data['estate'].unique().tolist())
    selected_estate = st.sidebar.selectbox("Pilih Estate", estate_list, key="heatmap_estate")
    
    # Filter Status
    status_filter = st.sidebar.multiselect(
        "Filter Status Produktivitas",
        options=["Critical", "Underperform", "Optimal"],
        default=["Critical", "Underperform", "Optimal"],
        key="heatmap_status"
    )
    
    # =============================
    # APPLY FILTERS
    # =============================
    filtered_data = data.copy()
    
    if selected_estate != "Semua Estate":
        filtered_data = filtered_data[filtered_data['estate'] == selected_estate]
    
    if status_filter:
        filtered_data = filtered_data[filtered_data['status'].isin(status_filter)]
    
    # =============================
    # HEADER
    # =============================
    st.header("🔥 Productivity Heatmap")
    st.caption("Visualisasi produktivitas per blok dan afdeling")
    
    # =============================
    # SUMMARY METRICS
    # =============================
    st.subheader("📊 Summary Statistics")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    total_blocks = len(filtered_data)
    total_area = filtered_data['luas_ha'].sum()
    avg_productivity = filtered_data['produktivitas'].mean()
    max_productivity = filtered_data['produktivitas'].max()
    min_productivity = filtered_data['produktivitas'].min()
    
    with col1:
        st.metric("Total Blocks", f"{total_blocks:,}")
    with col2:
        st.metric("Total Area (Ha)", f"{total_area:,.2f}")
    with col3:
        st.metric("Avg Productivity", f"{avg_productivity:.2f} Ton/Ha")
    with col4:
        st.metric("Max Productivity", f"{max_productivity:.2f} Ton/Ha")
    with col5:
        st.metric("Min Productivity", f"{min_productivity:.2f} Ton/Ha")
    
    # =============================
    # HEATMAP
    # =============================
    # Prepare heatmap data
    heatmap_data = filtered_data.pivot_table(
        index="afdeling",
        columns="blok",
        values="produktivitas",
        aggfunc="mean"
    )
    
    # Sort for better display
    heatmap_data = heatmap_data.sort_index()
    heatmap_data = heatmap_data.reindex(sorted(heatmap_data.columns), axis=1)
    
    # Create heatmap
    fig = px.imshow(
        heatmap_data,
        color_continuous_scale="RdYlGn",
        aspect="auto",
        labels=dict(x="Block", y="Afdeling", color="Ton/Ha"),
        zmin=0,
        zmax=30,
        title="Productivity Heatmap per Block"
    )
    
    fig.update_layout(height=600, font=dict(size=12))
    fig.update_traces(text=heatmap_data.values.round(1), texttemplate="%{text}")
    
    st.plotly_chart(fig, use_container_width=True)
    
    # =============================
    # STATUS DISTRIBUTION CHART
    # =============================
    st.subheader("📈 Productivity Status Distribution")
    
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        # Pie chart status
        status_counts = filtered_data['status'].value_counts().reset_index()
        status_counts.columns = ['Status', 'Count']
        
        color_map = {
            "Optimal": "#2ecc71",
            "Underperform": "#f1c40f",
            "Critical": "#e74c3c"
        }
        
        fig_pie = px.pie(
            status_counts,
            names="Status",
            values="Count",
            title="Block Classification Distribution",
            color="Status",
            color_discrete_map=color_map,
            hole=0.3
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col_chart2:
        # Bar chart per afdeling
        afdeling_stats = filtered_data.groupby('afdeling').agg({
            'produktivitas': 'mean',
            'blok': 'count'
        }).reset_index()
        afdeling_stats.columns = ['Afdeling', 'Rata-rata Produktivitas', 'Jumlah Blok']
        
        fig_bar = px.bar(
            afdeling_stats,
            x="Afdeling",
            y="Rata-rata Produktivitas",
            title="Average Productivity by Afdeling",
            color="Rata-rata Produktivitas",
            color_continuous_scale="RdYlGn",
            text="Rata-rata Produktivitas"
        )
        fig_bar.update_traces(texttemplate="%{text:.1f}", textposition="outside")
        fig_bar.update_layout(height=400)
        st.plotly_chart(fig_bar, use_container_width=True)
    
    # =============================
    # TOP PERFORMERS TABLES
    # =============================
    st.subheader("🏆 Block Performance Rankings")
    
    col_table1, col_table2 = st.columns(2)
    
    with col_table1:
        # Top 10 worst blocks
        worst_blocks = filtered_data.nsmallest(10, 'produktivitas')[['blok', 'estate', 'afdeling', 'luas_ha', 'produktivitas']]
        worst_blocks['produktivitas'] = worst_blocks['produktivitas'].round(2)
        worst_blocks.columns = ['Blok', 'Estate', 'Afdeling', 'Luas (Ha)', 'Produktivitas (Ton/Ha)']
        st.dataframe(worst_blocks, use_container_width=True)
        st.caption("🔴 Top 10 Blok dengan Produktivitas Terendah")
    
    with col_table2:
        # Top 10 best blocks
        best_blocks = filtered_data.nlargest(10, 'produktivitas')[['blok', 'estate', 'afdeling', 'luas_ha', 'produktivitas']]
        best_blocks['produktivitas'] = best_blocks['produktivitas'].round(2)
        best_blocks.columns = ['Blok', 'Estate', 'Afdeling', 'Luas (Ha)', 'Produktivitas (Ton/Ha)']
        st.dataframe(best_blocks, use_container_width=True)
        st.caption("🟢 Top 10 Blok dengan Produktivitas Tertinggi")
    
    # =============================
    # RECOMMENDATIONS
    # =============================
    st.subheader("💡 Recommendations for Decision Making")
    
    critical_count = len(filtered_data[filtered_data['produktivitas'] < CRITICAL_MAX])
    under_count = len(filtered_data[(filtered_data['produktivitas'] >= CRITICAL_MAX) & (filtered_data['produktivitas'] < OPTIMAL_MIN)])
    optimal_count = len(filtered_data[filtered_data['produktivitas'] >= OPTIMAL_MIN])
    
    col_rec1, col_rec2 = st.columns(2)
    
    with col_rec1:
        if critical_count > 0:
            st.warning(f"🔴 **Critical Priority ({critical_count} blocks)** - Produktivitas < 17 ton/ha")
        if under_count > 0:
            st.info(f"🟡 **Underperform Priority ({under_count} blocks)** - Produktivitas 17-22 ton/ha")
    
    with col_rec2:
        if optimal_count > 0:
            st.success(f"🟢 **Optimal Performance ({optimal_count} blocks)** - Produktivitas > 22 ton/ha")
        
        target = 25
        total_loss = ((target - filtered_data['produktivitas']).clip(lower=0) * filtered_data['luas_ha']).sum()
        if total_loss > 0:
            st.metric("📉 Estimated Production Loss", f"{total_loss:,.1f} Ton")
    
    # =============================
    # EXPORT DATA
    # =============================
    st.subheader("📎 Export Data")
    
    col_export1, col_export2 = st.columns(2)
    
    with col_export1:
        csv_data = heatmap_data.reset_index().to_csv(index=False)
        st.download_button("📥 Download Heatmap Data (CSV)", csv_data, "productivity_heatmap.csv", "text/csv", use_container_width=True)
    
    with col_export2:
        export_df = filtered_data[['estate', 'afdeling', 'blok', 'luas_ha', 'produktivitas', 'status']].copy()
        export_df.columns = ['Estate', 'Afdeling', 'Block', 'Area (Ha)', 'Productivity (Ton/Ha)', 'Status']
        csv_full = export_df.to_csv(index=False)
        st.download_button("📥 Download Full Data (CSV)", csv_full, "productivity_data.csv", "text/csv", use_container_width=True)
