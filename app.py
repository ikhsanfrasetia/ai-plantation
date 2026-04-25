import os
import streamlit as st
import plotly.express as px
import pandas as pd

from modules.auth import (
    init_auth_db,
    register_user,
    authenticate_user,
    get_pending_users,
    approve_user,
    reject_user,
    log_import,
    get_import_logs,
    save_uploaded_file,
    delete_import_log,
    get_all_users,
    admin_create_user,
    admin_update_user,
    admin_delete_user,
)

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
# AUTH INIT
# =============================
init_auth_db()

if "user" not in st.session_state:
    st.session_state.user = None

if "mode" not in st.session_state:
    st.session_state.mode = "login"


def show_auth_page():
    st.title(f"{APP_ICON} {APP_TITLE}")
    st.caption("Enterprise Analytics System for Palm Plantation Management")
    st.markdown("---")

    col_a, col_b = st.columns(2)

    with col_a:
        if st.button("🔐 Login", use_container_width=True):
            st.session_state.mode = "login"

    with col_b:
        if st.button("📝 Registrasi", use_container_width=True):
            st.session_state.mode = "register"

    st.markdown("---")

    if st.session_state.mode == "login":
        st.subheader("Login Pengguna")
        with st.form("login_form"):
            email = st.text_input("Alamat Email")
            password = st.text_input("Password", type="password")
            submit_login = st.form_submit_button("Masuk")
        if submit_login:
            ok, msg, user = authenticate_user(email.strip(), password)
            if ok:
                st.session_state.user = user
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)

    else:
        st.subheader("Registrasi Pengguna")
        with st.form("register_form"):
            nama = st.text_input("Nama")
            email = st.text_input("Alamat Email")
            no_hp = st.text_input("Nomor Hp")
            password = st.text_input("Password", type="password")
            submit_register = st.form_submit_button("Daftar")
        if submit_register:
            if not nama.strip() or not email.strip() or not no_hp.strip() or not password:
                st.warning("Semua field wajib diisi.")
            else:
                ok, msg = register_user(
                    nama=nama.strip(),
                    email=email.strip().lower(),
                    no_hp=no_hp.strip(),
                    password=password,
                )
                if ok:
                    st.success(msg)
                    st.session_state.mode = "login"
                else:
                    st.error(msg)


if st.session_state.user is None:
    show_auth_page()
    st.stop()

# =============================
# SIDEBAR
# =============================
st.sidebar.title(f"{APP_ICON} {APP_TITLE}")
st.sidebar.success(f"Login sebagai: {st.session_state.user['nama']}")
st.sidebar.caption(f"{st.session_state.user['email']}")

if st.sidebar.button("🚪 Logout", use_container_width=True):
    st.session_state.user = None
    st.rerun()

menu_items = [
    "Executive Dashboard",
    "Estate Analysis",
    "Block Analysis",
    "AI Block Intelligence",
    "Productivity Heatmap",
    "Production Forecast",
]

if st.session_state.user.get("role") == "admin":
    menu_items = ["Admin Portal"] + menu_items

menu = st.sidebar.radio("Navigation", menu_items)

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
# ADMIN PORTAL
# =============================
if menu == "Admin Portal" and st.session_state.user.get("role") == "admin":
    st.subheader("🛡️ Admin Portal")
    admin_submenu = st.radio(
        "Sub Menu",
        ["Approval Pengguna", "User Management", "Import Logs"],
        horizontal=True,
        key="admin_submenu"
    )

    if admin_submenu == "Approval Pengguna":
        st.markdown("### 1) Approval Pengguna")
        pending_users = get_pending_users()

        if pending_users:
            pending_table = pd.DataFrame(
                [
                    {
                        "ID": u.get("id"),
                        "Nama": u.get("nama"),
                        "Email": u.get("email"),
                        "No HP": u.get("no_hp"),
                        "Terdaftar": u.get("created_at"),
                    }
                    for u in pending_users
                ]
            )
            st.dataframe(pending_table, use_container_width=True, hide_index=True)

            selected_pending_id = st.selectbox(
                "Pilih User Pending",
                options=[u.get("id") for u in pending_users],
                format_func=lambda x: f"User #{x}",
                key="pending_user_select"
            )
            selected_pending = next((u for u in pending_users if u.get("id") == selected_pending_id), None)

            if selected_pending:
                st.info(
                    f"User terpilih: {selected_pending.get('nama')} "
                    f"({selected_pending.get('email')})"
                )
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("✅ Approve", key="btn_pending_approve", use_container_width=True):
                        approve_user(int(selected_pending_id))
                        st.success(f"User {selected_pending.get('email')} di-approve.")
                        st.rerun()
                with c2:
                    if st.button("❌ Reject", key="btn_pending_reject", use_container_width=True):
                        reject_user(int(selected_pending_id))
                        st.warning(f"User {selected_pending.get('email')} ditolak/dihapus.")
                        st.rerun()
        else:
            st.info("Tidak ada user pending.")

    elif admin_submenu == "User Management":
        st.markdown("### 2) User Management (CRUD)")
        users = get_all_users(limit=500)

        if users:
            user_table = pd.DataFrame(
                [
                    {
                        "ID": u.get("id"),
                        "Nama": u.get("nama"),
                        "Email": u.get("email"),
                        "No HP": u.get("no_hp"),
                        "Role": u.get("role"),
                        "Status": u.get("status"),
                        "Password": u.get("password_info", "Set (hashed)"),
                        "Created At": u.get("created_at"),
                        "Approved At": u.get("approved_at"),
                        "Setting": "⚙️ Klik detail",
                    }
                    for u in users
                ]
            )
            st.dataframe(user_table, use_container_width=True, hide_index=True)

            with st.expander("➕ Tambah Akun Baru", expanded=False):
                with st.form("admin_create_user_form"):
                    c1, c2 = st.columns(2)
                    with c1:
                        new_nama = st.text_input("Nama")
                        new_email = st.text_input("Email")
                        new_nohp = st.text_input("Nomor HP")
                    with c2:
                        new_password = st.text_input("Password", type="password")
                        new_role = st.selectbox("Role", ["user", "admin"])
                        new_status = st.selectbox("Status", ["approved", "pending"])
                    submit_new = st.form_submit_button("Simpan User")
                    if submit_new:
                        ok, msg = admin_create_user(
                            nama=new_nama,
                            email=new_email,
                            no_hp=new_nohp,
                            password=new_password,
                            role=new_role,
                            status=new_status,
                        )
                        if ok:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)

            st.markdown("#### ⚙️ Kolom Setting (Detail / Edit / Hapus)")
            selected_user_id = st.selectbox(
                "Pilih User ID",
                options=[u.get("id") for u in users],
                format_func=lambda x: f"User #{x}",
                key="admin_user_select"
            )
            selected_user = next((u for u in users if u.get("id") == selected_user_id), None)

            if selected_user:
                if st.button("⚙️ Buka Setting User", key="open_user_setting_modal", use_container_width=True):
                    st.session_state.show_user_setting_modal = True

                if "show_user_setting_modal" not in st.session_state:
                    st.session_state.show_user_setting_modal = False

                if st.session_state.show_user_setting_modal:
                    @st.dialog("Detail User & Aksi")
                    def user_setting_dialog():
                        st.markdown("##### Informasi Detail User")
                        detail_cols = st.columns(4)
                        detail_cols[0].metric("Nama", selected_user.get("nama", "-"))
                        detail_cols[1].metric("Role", selected_user.get("role", "-"))
                        detail_cols[2].metric("Status", selected_user.get("status", "-"))
                        detail_cols[3].metric("ID", str(selected_user.get("id", "-")))
                        st.caption(
                            f"Email: {selected_user.get('email', '-')} | "
                            f"No HP: {selected_user.get('no_hp', '-')} | "
                            f"Created: {selected_user.get('created_at', '-')} | "
                            f"Password: {selected_user.get('password_info', 'Set (hashed)')}"
                        )

                        with st.form("admin_edit_user_form"):
                            c1, c2 = st.columns(2)
                            with c1:
                                edit_nama = st.text_input("Nama", value=selected_user.get("nama", ""))
                                edit_email = st.text_input("Email", value=selected_user.get("email", ""))
                                edit_nohp = st.text_input("Nomor HP", value=selected_user.get("no_hp", ""))
                            with c2:
                                edit_role = st.selectbox(
                                    "Role",
                                    ["user", "admin"],
                                    index=0 if selected_user.get("role") == "user" else 1
                                )
                                edit_status = st.selectbox(
                                    "Status",
                                    ["approved", "pending"],
                                    index=0 if selected_user.get("status") == "approved" else 1
                                )
                                edit_password = st.text_input("Reset Password Baru (opsional)", type="password")

                            col_save, col_delete = st.columns(2)
                            with col_save:
                                submit_edit = st.form_submit_button("💾 Simpan Perubahan")
                            with col_delete:
                                submit_delete = st.form_submit_button("🗑️ Hapus Akun")

                            if submit_edit:
                                ok, msg = admin_update_user(
                                    user_id=int(selected_user_id),
                                    nama=edit_nama,
                                    email=edit_email,
                                    no_hp=edit_nohp,
                                    role=edit_role,
                                    status=edit_status,
                                    password=edit_password if edit_password else None,
                                )
                                if ok:
                                    st.session_state.show_user_setting_modal = False
                                    st.success(msg)
                                    st.rerun()
                                else:
                                    st.error(msg)

                            if submit_delete:
                                ok, msg = admin_delete_user(
                                    user_id=int(selected_user_id),
                                    current_admin_id=int(st.session_state.user["id"])
                                )
                                if ok:
                                    st.session_state.show_user_setting_modal = False
                                    st.success(msg)
                                    st.rerun()
                                else:
                                    st.error(msg)

                        if st.button("Tutup", key="close_user_setting_dialog"):
                            st.session_state.show_user_setting_modal = False
                            st.rerun()

                    user_setting_dialog()
        else:
            st.info("Belum ada user terdaftar.")

    else:
        st.markdown("### 3) Import Logs")
        logs = get_import_logs(limit=300)

        if logs:
            logs_df = pd.DataFrame(
                [
                    {
                        "ID": row.get("id"),
                        "User": row.get("user_email", "-"),
                        "File": row.get("filename", "-"),
                        "Ukuran (bytes)": row.get("file_size", 0),
                        "Waktu Import": row.get("imported_at", "-"),
                        "Catatan": row.get("notes", "-"),
                        "Status File": "Ada" if (row.get("stored_path") and os.path.exists(row.get("stored_path"))) else "Tidak Ada",
                        "Unduh": "⬇️",
                    }
                    for row in logs
                ]
            )
            st.dataframe(logs_df, use_container_width=True, hide_index=True)

            selected_id = st.selectbox(
                "Pilih Log ID",
                options=[r.get("id") for r in logs],
                format_func=lambda x: f"Log #{x}",
                key="admin_log_select"
            )
            selected_row = next((r for r in logs if r.get("id") == selected_id), None)

            c1, c2 = st.columns(2)
            with c1:
                if selected_row:
                    stored_path = selected_row.get("stored_path")
                    if stored_path and os.path.exists(stored_path):
                        with open(stored_path, "rb") as f:
                            st.download_button(
                                label="⬇️ Unduh Data",
                                data=f.read(),
                                file_name=selected_row.get("filename", "uploaded_file.xlsx"),
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                key=f"admin_dl_{selected_id}",
                                use_container_width=True,
                            )
                    else:
                        st.button("⬇️ Unduh Data", disabled=True, use_container_width=True)
                        st.warning("File fisik untuk log ini tidak ditemukan.")
            with c2:
                if st.button("🗑️ Hapus Log", key=f"admin_delete_{selected_id}", use_container_width=True):
                    ok, msg = delete_import_log(int(selected_id), delete_file=True)
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
        else:
            st.info("Belum ada log import.")

    st.stop()

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

        saved_ok, save_msg, stored_path, file_size = save_uploaded_file(st.session_state.user, file)
        if not saved_ok:
            st.error(save_msg)
            st.stop()

        log_import(
            user=st.session_state.user,
            filename=file.name if file is not None else "unknown.xlsx",
            file_size=file_size if file_size is not None else 0,
            notes="Upload, simpan file, dan parse excel dari sidebar",
            stored_path=stored_path,
        )

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