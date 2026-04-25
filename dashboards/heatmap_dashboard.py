import streamlit as st
import plotly.express as px
import pandas as pd
import numpy as np

# =============================
# FUNGSI HITUNG POTENSI & PERFORMA
# =============================
def hitung_potensi_dan_performa(df_master_block, df_produksi_bulanan, df_parameter, tahun_sekarang=2025):
    """
    Menghitung potensi, real produksi, dan performa setiap blok
    """
    # 1. Hitung real produksi per blok (kg/tahun)
    produksi_tahunan = df_produksi_bulanan.groupby(['estate', 'afdeling', 'blok'])['produksi_tbs_kg'].sum().reset_index()
    produksi_tahunan.rename(columns={'produksi_tbs_kg': 'real_kg_tahun'}, inplace=True)
    
    # 2. Gabung dengan master block
    df = df_master_block.merge(produksi_tahunan, on=['estate', 'afdeling', 'blok'], how='left')
    
    # 3. Hitung umur tanaman
    df['umur'] = tahun_sekarang - df['tahun_tanam']
    
    # 4. Mapping potensi berdasarkan umur dari sheet PARAMETER
    def get_potensi(umur):
        for _, row in df_parameter.iterrows():
            if row['umur_min'] <= umur <= row['umur_max']:
                return row['potensi_ton_ha']
        return None
    
    df['potensi_ton_ha'] = df['umur'].apply(get_potensi)
    
    # 5. Hitung real produktivitas (ton/ha)
    df['real_ton_ha'] = (df['real_kg_tahun'] / 1000) / df['luas_ha']
    df['real_ton_ha'] = df['real_ton_ha'].round(2)
    
    # 6. Hitung rasio real vs potensi (%)
    df['rasio_potensi'] = (df['real_ton_ha'] / df['potensi_ton_ha'] * 100).round(1)
    
    # 7. Klasifikasi performa berdasarkan rasio
    def klasifikasi_performa(rasio):
        if pd.isna(rasio):
            return "Tidak Ada Data"
        elif rasio < 70:
            return "Critical (<70%)"
        elif rasio < 90:
            return "Underperform (70-90%)"
        else:
            return "Optimal (≥90%)"
    
    df['kategori_performa'] = df['rasio_potensi'].apply(klasifikasi_performa)
    
    # 8. Klasifikasi berdasarkan nilai absolut (untuk kompatibilitas)
    df['produktivitas'] = df['real_ton_ha']
    
    df['status'] = df['real_ton_ha'].apply(
        lambda x: "Optimal" if x >= 22
        else "Underperform" if x >= 17
        else "Critical" if pd.notna(x)
        else "Tidak Ada Data"
    )
    
    return df


# =============================
# FUNGSI MAIN HEATMAP
# =============================
def show_heatmap(data, param_df=None, master_df=None, produksi_df=None):
    """
    Menampilkan productivity heatmap dengan fitur lengkap dan tampilan rapi
    """
    
    # =============================
    # HITUNG POTENSI & PERFORMA
    # =============================
    if param_df is not None and master_df is not None and produksi_df is not None:
        df_analysis = hitung_potensi_dan_performa(master_df, produksi_df, param_df)
        data = df_analysis
        st.success(f"✅ Data berhasil diproses! Total {len(data)} blok dianalisis.")
    
    # Cek apakah data kosong
    if data is None or len(data) == 0:
        st.error("❌ Tidak ada data untuk ditampilkan. Periksa kembali file Excel Anda.")
        return
    
    # =============================
    # KONFIGURASI
    # =============================
    CRITICAL_MAX = 17
    OPTIMAL_MIN = 22
    
    # =============================
    # SIDEBAR FILTERS
    # =============================
    with st.sidebar:
        st.markdown("---")
        st.markdown("### 🎯 Filter Data")
        
        # Filter Estate
        estate_list = ["Semua Estate"] + sorted(data['estate'].unique().tolist())
        selected_estate = st.selectbox("📍 Pilih Estate", estate_list, key="heatmap_estate")
        
        # Filter Status Absolut
        if 'status' in data.columns:
            status_filter = st.multiselect(
                "🏷️ Filter Status (Ton/Ha Absolut)",
                options=["Critical", "Underperform", "Optimal"],
                default=["Critical", "Underperform", "Optimal"],
                key="heatmap_status"
            )
        else:
            status_filter = []
        
        st.markdown("---")
        st.markdown("### 🎯 Filter Performa (Real vs Potensi)")
        
        # Filter Performa
        performa_filter = st.multiselect(
            "📊 Filter Kategori Performa",
            options=["Critical (<70%)", "Underperform (70-90%)", "Optimal (≥90%)", "Tidak Ada Data"],
            default=["Critical (<70%)", "Underperform (70-90%)", "Optimal (≥90%)"],
            key="performa_filter"
        )
    
    # =============================
    # APPLY FILTERS
    # =============================
    filtered_data = data.copy()
    
    if selected_estate != "Semua Estate":
        filtered_data = filtered_data[filtered_data['estate'] == selected_estate]
    
    if status_filter and 'status' in filtered_data.columns:
        filtered_data = filtered_data[filtered_data['status'].isin(status_filter)]
    
    if performa_filter:
        if 'kategori_performa' in filtered_data.columns:
            filtered_data = filtered_data[filtered_data['kategori_performa'].isin(performa_filter)]
    
    # =============================
    # HEADER
    # =============================
    st.markdown("# 🔥 Productivity Heatmap Dashboard")
    st.markdown("---")
    
    # =============================
    # SUMMARY METRICS - 5 COLUMNS
    # =============================
    col1, col2, col3, col4, col5 = st.columns(5, gap="small")
    
    total_blocks = len(filtered_data)
    total_area = filtered_data['luas_ha'].sum()
    avg_productivity = filtered_data['real_ton_ha'].mean()
    max_productivity = filtered_data['real_ton_ha'].max()
    min_productivity = filtered_data['real_ton_ha'].min()
    
    with col1:
        st.metric("📦 Total Blocks", f"{total_blocks:,}")
    with col2:
        st.metric("🌾 Total Area (Ha)", f"{total_area:,.2f}")
    with col3:
        st.metric("📊 Avg Productivity", f"{avg_productivity:.2f} Ton/Ha")
    with col4:
        st.metric("📈 Max Productivity", f"{max_productivity:.2f} Ton/Ha")
    with col5:
        st.metric("📉 Min Productivity", f"{min_productivity:.2f} Ton/Ha")
    
    st.markdown("---")
    
    # =============================
    # HEATMAP
    # =============================
    st.subheader("🗺️ Visualisasi Heatmap (Real Produktivitas)")
    
    heatmap_data = filtered_data.pivot_table(
        index="afdeling",
        columns="blok",
        values="real_ton_ha",
        aggfunc="mean"
    )
    
    if not heatmap_data.empty:
        heatmap_data = heatmap_data.sort_index()
        heatmap_data = heatmap_data.reindex(sorted(heatmap_data.columns), axis=1)
        
        fig = px.imshow(
            heatmap_data,
            color_continuous_scale="RdYlGn",
            aspect="auto",
            labels=dict(x="Block", y="Afdeling", color="Ton/Ha"),
            zmin=0,
            zmax=40,
            title="<b>Productivity Heatmap per Block (Real Production)</b>"
        )
        
        fig.update_layout(height=550, font=dict(size=12))
        fig.update_traces(text=heatmap_data.values.round(1), texttemplate=None, textfont_size=10)
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("⚠️ Tidak cukup data untuk membuat heatmap")
    
    # =============================
    # TABLE REAL VS POTENSI
    # =============================
    st.markdown("---")
    st.subheader("📊 Real vs Potential Analysis")
    st.caption("Perbandingan produksi real dengan potensi berdasarkan umur tanaman")
    
    # Tampilkan tabel perbandingan
    comparison_cols = ['blok', 'afdeling', 'luas_ha', 'umur', 'potensi_ton_ha', 'real_ton_ha', 'rasio_potensi', 'kategori_performa']
    comparison_data = filtered_data[comparison_cols].copy()
    comparison_data = comparison_data.sort_values('rasio_potensi', ascending=False)
    
    # Rename columns for better display
    comparison_data.columns = ['Blok', 'Afdeling', 'Luas (Ha)', 'Umur (Tahun)', 'Potensi (Ton/Ha)', 'Real (Ton/Ha)', 'Rasio (%)', 'Kategori']
    
    st.dataframe(
        comparison_data,
        use_container_width=True,
        hide_index=True,
        column_config={
            'Blok': 'Blok',
            'Afdeling': 'Afdeling',
            'Luas (Ha)': st.column_config.NumberColumn('Luas (Ha)', format='%.2f'),
            'Umur (Tahun)': 'Umur (Tahun)',
            'Potensi (Ton/Ha)': st.column_config.NumberColumn('Potensi (Ton/Ha)', format='%.1f'),
            'Real (Ton/Ha)': st.column_config.NumberColumn('Real (Ton/Ha)', format='%.1f'),
            'Rasio (%)': st.column_config.NumberColumn('Rasio (%)', format='%.1f'),
            'Kategori': 'Kategori'
        }
    )
    
    # Metric ringkasan performa
    st.markdown("#### 📈 Ringkasan Performa Real vs Potensi")
    
    col_perf1, col_perf2, col_perf3, col_perf4 = st.columns(4)
    
    above_potensi = len(filtered_data[filtered_data['rasio_potensi'] >= 100])
    optimal_perf = len(filtered_data[filtered_data['kategori_performa'] == "Optimal (≥90%)"])
    under_perf = len(filtered_data[filtered_data['kategori_performa'] == "Underperform (70-90%)"])
    critical_perf = len(filtered_data[filtered_data['kategori_performa'] == "Critical (<70%)"])
    
    with col_perf1:
        st.metric("✅ Above Potential", f"{above_potensi} block", 
                  help="Real produksi ≥ potensi (≥100%)")
    with col_perf2:
        st.metric("🟢 Optimal (≥90%)", f"{optimal_perf} block")
    with col_perf3:
        st.metric("🟡 Underperform (70-90%)", f"{under_perf} block")
    with col_perf4:
        st.metric("🔴 Critical (<70%)", f"{critical_perf} block")
    
    # =============================
    # DUAL CHARTS: PIE & BAR
    # =============================
    st.markdown("---")
    st.subheader("📊 Analisis Distribusi")
    
    col_chart1, col_chart2 = st.columns(2, gap="medium")
    
    with col_chart1:
        st.markdown("#### 🥧 Distribusi Status (Ton/Ha Absolut)")
        if 'status' in filtered_data.columns:
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
                title="Klasifikasi Blok (Ton/Ha Absolut)",
                color="Status",
                color_discrete_map=color_map,
                hole=0.4
            )
            fig_pie.update_traces(textposition="inside", textinfo="percent+label")
            fig_pie.update_layout(height=400)
            st.plotly_chart(fig_pie, use_container_width=True)
    
    with col_chart2:
        st.markdown("#### 🥧 Distribusi Performa (Real vs Potensi)")
        performa_counts = filtered_data['kategori_performa'].value_counts().reset_index()
        performa_counts.columns = ['Kategori', 'Count']
        
        color_map_performa = {
            "Optimal (≥90%)": "#2ecc71",
            "Underperform (70-90%)": "#f1c40f",
            "Critical (<70%)": "#e74c3c",
            "Tidak Ada Data": "#95a5a6"
        }
        
        fig_pie_performa = px.pie(
            performa_counts,
            names="Kategori",
            values="Count",
            title="Klasifikasi Performa (Real vs Potensi)",
            color="Kategori",
            color_discrete_map=color_map_performa,
            hole=0.4
        )
        fig_pie_performa.update_traces(textposition="inside", textinfo="percent+label")
        fig_pie_performa.update_layout(height=400)
        st.plotly_chart(fig_pie_performa, use_container_width=True)
    
    # Bar chart perbandingan per afdeling
    st.markdown("#### 📊 Perbandingan Real vs Potensi per Afdeling")
    
    afdeling_stats = filtered_data.groupby('afdeling').agg({
        'real_ton_ha': 'mean',
        'potensi_ton_ha': 'mean',
        'blok': 'count'
    }).reset_index()
    afdeling_stats.columns = ['Afdeling', 'Rata-rata Real', 'Rata-rata Potensi', 'Jumlah Blok']
    
    afdeling_melted = afdeling_stats.melt(
        id_vars=['Afdeling'], 
        value_vars=['Rata-rata Real', 'Rata-rata Potensi'],
        var_name='Tipe', 
        value_name='Produktivitas'
    )
    
    fig_bar_group = px.bar(
        afdeling_melted,
        x="Afdeling",
        y="Produktivitas",
        color="Tipe",
        barmode="group",
        title="Perbandingan Real vs Potensi per Afdeling",
        color_discrete_map={
            "Rata-rata Real": "#3498db",
            "Rata-rata Potensi": "#2ecc71"
        },
        text="Produktivitas"
    )
    fig_bar_group.update_traces(texttemplate="%{text:.1f}", textposition="outside")
    fig_bar_group.update_layout(height=450, xaxis_tickangle=-45)
    st.plotly_chart(fig_bar_group, use_container_width=True)
    
    # =============================
    # TOP PERFORMERS TABLES
    # =============================
    st.markdown("---")
    st.subheader("🏆 Peringkat Blok Berdasarkan Rasio Real vs Potensi")
    
    col_table1, col_table2 = st.columns(2, gap="medium")
    
    with col_table1:
        st.markdown("#### 🔴 10 Rasio Terendah (Perlu Perhatian)")
        worst_ratio = filtered_data.nsmallest(10, 'rasio_potensi')[
            ['blok', 'estate', 'afdeling', 'potensi_ton_ha', 'real_ton_ha', 'rasio_potensi']
        ]
        worst_ratio.columns = ['Blok', 'Estate', 'Afdeling', 'Potensi', 'Real', 'Rasio (%)']
        worst_ratio['Rasio (%)'] = worst_ratio['Rasio (%)'].round(1)
        st.dataframe(worst_ratio, use_container_width=True, hide_index=True)
    
    with col_table2:
        st.markdown("#### 🟢 10 Rasio Tertinggi (Best Performance)")
        best_ratio = filtered_data.nlargest(10, 'rasio_potensi')[
            ['blok', 'estate', 'afdeling', 'potensi_ton_ha', 'real_ton_ha', 'rasio_potensi']
        ]
        best_ratio.columns = ['Blok', 'Estate', 'Afdeling', 'Potensi', 'Real', 'Rasio (%)']
        best_ratio['Rasio (%)'] = best_ratio['Rasio (%)'].round(1)
        st.dataframe(best_ratio, use_container_width=True, hide_index=True)
    
    # =============================
    # RECOMMENDATIONS
    # =============================
    st.markdown("---")
    st.subheader("💡 Rekomendasi Tindakan Berdasarkan Performa")
    
    critical_perf_data = filtered_data[filtered_data['kategori_performa'] == "Critical (<70%)"]
    under_perf_data = filtered_data[filtered_data['kategori_performa'] == "Underperform (70-90%)"]
    optimal_perf_data = filtered_data[filtered_data['kategori_performa'] == "Optimal (≥90%)"]
    
    critical_count = len(critical_perf_data)
    under_count = len(under_perf_data)
    optimal_count = len(optimal_perf_data)
    
    col_rec1, col_rec2, col_rec3 = st.columns(3, gap="medium")
    
    with col_rec1:
        if critical_count > 0:
            st.markdown(f"""
            <div style="background-color:#fff5f5; padding:15px; border-radius:10px; border-left:5px solid #e74c3c;">
            <h4 style="color:#e74c3c; margin:0 0 10px 0;">🔴 Critical ({critical_count})</h4>
            <p style="margin:0; font-size:14px;">Real &lt; 70% dari potensi</p>
            <hr style="margin:10px 0;">
            <p style="margin:0; font-size:13px;">✅ Evaluasi kesuburan tanah<br>✅ Periksa hama & penyakit<br>✅ Optimalkan irigasi<br>✅ Review pemupukan</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="background-color:#f0fff0; padding:15px; border-radius:10px; border-left:5px solid #2ecc71;">
            <h4 style="color:#2ecc71; margin:0;">✅ Critical ({critical_count})</h4>
            <p style="margin:5px 0 0 0;">Tidak ada blok critical</p>
            </div>
            """, unsafe_allow_html=True)
    
    with col_rec2:
        if under_count > 0:
            st.markdown(f"""
            <div style="background-color:#fffbea; padding:15px; border-radius:10px; border-left:5px solid #f1c40f;">
            <h4 style="color:#f1c40f; margin:0 0 10px 0;">🟡 Underperform ({under_count})</h4>
            <p style="margin:0; font-size:14px;">Real 70-90% dari potensi</p>
            <hr style="margin:10px 0;">
            <p style="margin:0; font-size:13px;">✅ Tingkatkan pemupukan<br>✅ Optimalkan pemangkasan<br>✅ Perbaiki drainase<br>✅ Evaluasi jadwal panen</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="background-color:#f0fff0; padding:15px; border-radius:10px; border-left:5px solid #2ecc71;">
            <h4 style="color:#2ecc71; margin:0;">✅ Underperform ({under_count})</h4>
            <p style="margin:5px 0 0 0;">Tidak ada blok underperform</p>
            </div>
            """, unsafe_allow_html=True)
    
    with col_rec3:
        if optimal_count > 0:
            st.markdown(f"""
            <div style="background-color:#f3fff5; padding:15px; border-radius:10px; border-left:5px solid #2ecc71;">
            <h4 style="color:#2ecc71; margin:0 0 10px 0;">🟢 Optimal ({optimal_count})</h4>
            <p style="margin:0; font-size:14px;">Real ≥ 90% dari potensi</p>
            <hr style="margin:10px 0;">
            <p style="margin:0; font-size:13px;">✅ Pertahankan praktik baik<br>✅ Jadikan benchmark<br>✅ Dokumentasi best practice<br>✅ Replikasi ke afdeling lain</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="background-color:#fff5f5; padding:15px; border-radius:10px; border-left:5px solid #e74c3c;">
            <h4 style="color:#e74c3c; margin:0;">⚠️ Optimal ({optimal_count})</h4>
            <p style="margin:5px 0 0 0;">Belum ada blok optimal</p>
            </div>
            """, unsafe_allow_html=True)
    
    # =============================
    # EXPANDABLE LISTS PER KRITERIA
    # =============================
    st.markdown("---")
    st.subheader("📋 Daftar Blok per Klasifikasi Performa")
    st.caption("Klik tombol ▶️ di bawah untuk melihat detail blok pada setiap kategori")
    
    # Critical Blocks
    with st.expander(f"🔴 CRITICAL PERFORMANCE ({critical_count} blok) - Real < 70% dari Potensi", expanded=False):
        if critical_count > 0:
            critical_display = critical_perf_data[['estate', 'afdeling', 'blok', 'luas_ha', 'umur', 'potensi_ton_ha', 'real_ton_ha', 'rasio_potensi']].copy()
            critical_display = critical_display.sort_values('rasio_potensi', ascending=True)
            critical_display.columns = ['Estate', 'Afdeling', 'Blok', 'Luas (Ha)', 'Umur (Tahun)', 'Potensi (Ton/Ha)', 'Real (Ton/Ha)', 'Rasio (%)']
            st.dataframe(critical_display, use_container_width=True, hide_index=True)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Blok", critical_count)
            with col2:
                st.metric("Total Luas", f"{critical_perf_data['luas_ha'].sum():.2f} Ha")
            with col3:
                st.metric("Rata-rata Rasio", f"{critical_perf_data['rasio_potensi'].mean():.1f}%")
        else:
            st.success("✅ Tidak ada blok dengan performa Critical")
    
    # Underperform Blocks
    with st.expander(f"🟡 UNDERPERFORM ({under_count} blok) - Real 70-90% dari Potensi", expanded=False):
        if under_count > 0:
            under_display = under_perf_data[['estate', 'afdeling', 'blok', 'luas_ha', 'umur', 'potensi_ton_ha', 'real_ton_ha', 'rasio_potensi']].copy()
            under_display = under_display.sort_values('rasio_potensi', ascending=True)
            under_display.columns = ['Estate', 'Afdeling', 'Blok', 'Luas (Ha)', 'Umur (Tahun)', 'Potensi (Ton/Ha)', 'Real (Ton/Ha)', 'Rasio (%)']
            st.dataframe(under_display, use_container_width=True, hide_index=True)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Blok", under_count)
            with col2:
                st.metric("Total Luas", f"{under_perf_data['luas_ha'].sum():.2f} Ha")
            with col3:
                st.metric("Rata-rata Rasio", f"{under_perf_data['rasio_potensi'].mean():.1f}%")
        else:
            st.success("✅ Tidak ada blok dengan performa Underperform")
    
    # Optimal Blocks
    with st.expander(f"🟢 OPTIMAL ({optimal_count} blok) - Real ≥ 90% dari Potensi", expanded=False):
        if optimal_count > 0:
            optimal_display = optimal_perf_data[['estate', 'afdeling', 'blok', 'luas_ha', 'umur', 'potensi_ton_ha', 'real_ton_ha', 'rasio_potensi']].copy()
            optimal_display = optimal_display.sort_values('rasio_potensi', ascending=False)
            optimal_display.columns = ['Estate', 'Afdeling', 'Blok', 'Luas (Ha)', 'Umur (Tahun)', 'Potensi (Ton/Ha)', 'Real (Ton/Ha)', 'Rasio (%)']
            st.dataframe(optimal_display, use_container_width=True, hide_index=True)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Blok", optimal_count)
            with col2:
                st.metric("Total Luas", f"{optimal_perf_data['luas_ha'].sum():.2f} Ha")
            with col3:
                st.metric("Rata-rata Rasio", f"{optimal_perf_data['rasio_potensi'].mean():.1f}%")
        else:
            st.info("ℹ️ Tidak ada blok dengan performa Optimal")
    
    # =============================
    # INFO
    # =============================
    with st.expander("ℹ️ Informasi & Interpretasi"):
        st.markdown("""
        ### 🎨 Interpretasi Data
        
        | Kategori | Kriteria (Rasio Real vs Potensi) | Tindakan |
        |----------|----------------------------------|----------|
        | 🟢 **Optimal** | ≥ 90% | Pertahankan praktik baik, jadikan benchmark |
        | 🟡 **Underperform** | 70% - 90% | Perlu optimalisasi pemupukan & perawatan |
        | 🔴 **Critical** | < 70% | Perlu intervensi segera |
        
        ### 📌 Tips Penggunaan
        1. Gunakan filter di sidebar untuk memfilter Estate dan Kategori
        2. Lihat tabel **Real vs Potential Analysis** untuk perbandingan detail
        3. Hover pada heatmap untuk melihat nilai real produktivitas
        4. Klik expand pada daftar blok untuk melihat detail per kategori
        """)