import os
import sqlite3
import hashlib
from datetime import datetime
from typing import Optional, Tuple, Dict, Any

DB_PATH = "data/app.db"
UPLOAD_ROOT = "data/uploads"


def _get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def _hash_password(password: str, salt: str) -> str:
    return hashlib.sha256((salt + password).encode("utf-8")).hexdigest()


def init_auth_db() -> None:
    os.makedirs(UPLOAD_ROOT, exist_ok=True)

    conn = _get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nama TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            no_hp TEXT NOT NULL,
            password_salt TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user',
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TEXT NOT NULL,
            approved_at TEXT
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS import_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            user_email TEXT NOT NULL,
            filename TEXT NOT NULL,
            file_size INTEGER,
            imported_at TEXT NOT NULL,
            notes TEXT,
            stored_path TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        """
    )

    # Schema migration for existing database:
    # ensure 'stored_path' column exists on older import_logs tables.
    cur.execute("PRAGMA table_info(import_logs)")
    existing_cols = [r[1] for r in cur.fetchall()]
    if "stored_path" not in existing_cols:
        cur.execute("ALTER TABLE import_logs ADD COLUMN stored_path TEXT")

    conn.commit()
    conn.close()

    bootstrap_admin_from_env()


def bootstrap_admin_from_env() -> None:
    admin_email = os.getenv("ADMIN_EMAIL")
    admin_password = os.getenv("ADMIN_PASSWORD")
    admin_name = os.getenv("ADMIN_NAME", "Administrator")
    admin_phone = os.getenv("ADMIN_PHONE", "-")

    if not admin_email or not admin_password:
        return

    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE email = ?", (admin_email,))
    exists = cur.fetchone()

    if not exists:
        salt = os.urandom(16).hex()
        pwd_hash = _hash_password(admin_password, salt)
        now = datetime.utcnow().isoformat()
        cur.execute(
            """
            INSERT INTO users (nama, email, no_hp, password_salt, password_hash, role, status, created_at, approved_at)
            VALUES (?, ?, ?, ?, ?, 'admin', 'approved', ?, ?)
            """,
            (admin_name, admin_email, admin_phone, salt, pwd_hash, now, now),
        )
        conn.commit()

    conn.close()


def register_user(nama: str, email: str, no_hp: str, password: str) -> Tuple[bool, str]:
    conn = _get_conn()
    cur = conn.cursor()

    cur.execute("SELECT id FROM users WHERE email = ?", (email,))
    if cur.fetchone():
        conn.close()
        return False, "Email sudah terdaftar."

    salt = os.urandom(16).hex()
    pwd_hash = _hash_password(password, salt)
    now = datetime.utcnow().isoformat()

    cur.execute(
        """
        INSERT INTO users (nama, email, no_hp, password_salt, password_hash, role, status, created_at)
        VALUES (?, ?, ?, ?, ?, 'user', 'pending', ?)
        """,
        (nama, email, no_hp, salt, pwd_hash, now),
    )

    conn.commit()
    conn.close()
    return True, "Registrasi berhasil. Menunggu approval admin."


def authenticate_user(email: str, password: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE email = ?", (email,))
    row = cur.fetchone()
    conn.close()

    if not row:
        return False, "Email tidak ditemukan.", None

    pwd_hash = _hash_password(password, row["password_salt"])
    if pwd_hash != row["password_hash"]:
        return False, "Password salah.", None

    if row["status"] != "approved":
        return False, "Akun belum di-approve admin.", None

    user = {
        "id": row["id"],
        "nama": row["nama"],
        "email": row["email"],
        "no_hp": row["no_hp"],
        "role": row["role"],
        "status": row["status"],
    }
    return True, "Login berhasil.", user


def get_pending_users():
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, nama, email, no_hp, created_at FROM users WHERE status='pending' ORDER BY created_at ASC"
    )
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def approve_user(user_id: int) -> None:
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        "UPDATE users SET status='approved', approved_at=? WHERE id=?",
        (datetime.utcnow().isoformat(), user_id),
    )
    conn.commit()
    conn.close()


def reject_user(user_id: int) -> None:
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE id=?", (user_id,))
    conn.commit()
    conn.close()


def save_uploaded_file(user: Dict[str, Any], uploaded_file) -> Tuple[bool, str, Optional[str], Optional[int]]:
    if uploaded_file is None:
        return False, "File upload tidak ditemukan.", None, None

    user_dir = os.path.join(UPLOAD_ROOT, str(user["id"]))
    os.makedirs(user_dir, exist_ok=True)

    safe_name = os.path.basename(uploaded_file.name)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
    stored_name = f"{timestamp}_{safe_name}"
    stored_path = os.path.join(user_dir, stored_name)

    file_bytes = uploaded_file.getvalue()
    with open(stored_path, "wb") as f:
        f.write(file_bytes)

    return True, "File berhasil disimpan.", stored_path, len(file_bytes)


def log_import(user: Dict[str, Any], filename: str, file_size: int, notes: str = "", stored_path: Optional[str] = None) -> None:
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO import_logs (user_id, user_email, filename, file_size, imported_at, notes, stored_path)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user["id"],
            user["email"],
            filename,
            int(file_size) if file_size is not None else None,
            datetime.utcnow().isoformat(),
            notes,
            stored_path,
        ),
    )
    conn.commit()
    conn.close()


def get_import_logs(limit: int = 200):
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, user_id, user_email, filename, file_size, imported_at, notes, stored_path
        FROM import_logs
        ORDER BY imported_at DESC
        LIMIT ?
        """,
        (limit,),
    )
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def get_user_import_logs(user_id: int, limit: int = 200):
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, user_id, user_email, filename, file_size, imported_at, notes, stored_path
        FROM import_logs
        WHERE user_id = ?
        ORDER BY imported_at DESC
        LIMIT ?
        """,
        (user_id, limit),
    )
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def delete_import_log(log_id: int, delete_file: bool = True) -> Tuple[bool, str]:
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("SELECT stored_path FROM import_logs WHERE id = ?", (log_id,))
    row = cur.fetchone()

    if not row:
        conn.close()
        return False, "Log tidak ditemukan."

    stored_path = row["stored_path"]
    cur.execute("DELETE FROM import_logs WHERE id = ?", (log_id,))
    conn.commit()
    conn.close()

    if delete_file and stored_path:
        try:
            if os.path.exists(stored_path):
                os.remove(stored_path)
        except Exception:
            return False, "Log terhapus, tapi file fisik gagal dihapus."

    return True, "Log berhasil dihapus."


def get_all_users(limit: int = 500):
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, nama, email, no_hp, role, status, created_at, approved_at,
               CASE
                   WHEN password_hash IS NOT NULL AND password_hash <> '' THEN 'Set (hashed)'
                   ELSE 'Not set'
               END AS password_info
        FROM users
        ORDER BY created_at DESC
        LIMIT ?
        """,
        (limit,),
    )
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def admin_create_user(
    nama: str,
    email: str,
    no_hp: str,
    password: str,
    role: str = "user",
    status: str = "approved",
) -> Tuple[bool, str]:
    email = (email or "").strip().lower()
    nama = (nama or "").strip()
    no_hp = (no_hp or "").strip()

    if not nama or not email or not no_hp or not password:
        return False, "Semua field wajib diisi."

    if role not in ("admin", "user"):
        return False, "Role tidak valid."

    if status not in ("approved", "pending"):
        return False, "Status tidak valid."

    conn = _get_conn()
    cur = conn.cursor()

    cur.execute("SELECT id FROM users WHERE email = ?", (email,))
    if cur.fetchone():
        conn.close()
        return False, "Email sudah terdaftar."

    salt = os.urandom(16).hex()
    pwd_hash = _hash_password(password, salt)
    now = datetime.utcnow().isoformat()
    approved_at = now if status == "approved" else None

    cur.execute(
        """
        INSERT INTO users (nama, email, no_hp, password_salt, password_hash, role, status, created_at, approved_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (nama, email, no_hp, salt, pwd_hash, role, status, now, approved_at),
    )
    conn.commit()
    conn.close()
    return True, "User berhasil ditambahkan."


def admin_update_user(
    user_id: int,
    nama: str,
    email: str,
    no_hp: str,
    role: str,
    status: str,
    password: Optional[str] = None,
) -> Tuple[bool, str]:
    email = (email or "").strip().lower()
    nama = (nama or "").strip()
    no_hp = (no_hp or "").strip()

    if not nama or not email or not no_hp:
        return False, "Nama, email, dan no hp wajib diisi."

    if role not in ("admin", "user"):
        return False, "Role tidak valid."

    if status not in ("approved", "pending"):
        return False, "Status tidak valid."

    conn = _get_conn()
    cur = conn.cursor()

    cur.execute("SELECT id FROM users WHERE id = ?", (user_id,))
    current = cur.fetchone()
    if not current:
        conn.close()
        return False, "User tidak ditemukan."

    cur.execute("SELECT id FROM users WHERE email = ? AND id <> ?", (email, user_id))
    if cur.fetchone():
        conn.close()
        return False, "Email sudah digunakan user lain."

    approved_at = datetime.utcnow().isoformat() if status == "approved" else None

    if password:
        salt = os.urandom(16).hex()
        pwd_hash = _hash_password(password, salt)
        cur.execute(
            """
            UPDATE users
            SET nama=?, email=?, no_hp=?, role=?, status=?, approved_at=?, password_salt=?, password_hash=?
            WHERE id=?
            """,
            (nama, email, no_hp, role, status, approved_at, salt, pwd_hash, user_id),
        )
    else:
        cur.execute(
            """
            UPDATE users
            SET nama=?, email=?, no_hp=?, role=?, status=?, approved_at=?
            WHERE id=?
            """,
            (nama, email, no_hp, role, status, approved_at, user_id),
        )

    conn.commit()
    conn.close()
    return True, "User berhasil diperbarui."


def admin_delete_user(user_id: int, current_admin_id: int) -> Tuple[bool, str]:
    if int(user_id) == int(current_admin_id):
        return False, "Admin tidak boleh menghapus akun sendiri."

    conn = _get_conn()
    cur = conn.cursor()

    cur.execute("SELECT id FROM users WHERE id = ?", (user_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return False, "User tidak ditemukan."

    cur.execute("DELETE FROM import_logs WHERE user_id = ?", (user_id,))
    cur.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()

    user_dir = os.path.join(UPLOAD_ROOT, str(user_id))
    if os.path.exists(user_dir):
        try:
            for name in os.listdir(user_dir):
                path = os.path.join(user_dir, name)
                if os.path.isfile(path):
                    os.remove(path)
            os.rmdir(user_dir)
        except Exception:
            return False, "User terhapus, tetapi sebagian file upload tidak dapat dibersihkan."

    return True, "User berhasil dihapus."
