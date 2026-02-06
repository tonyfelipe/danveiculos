from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import sqlite3
import os
from datetime import datetime
from functools import wraps

# ================= CONFIGURAÇÃO BÁSICA =================

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "chave-dev")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")

UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}

# ================= BANCO =================

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vehicles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            marca TEXT NOT NULL,
            modelo TEXT NOT NULL,
            ano INTEGER NOT NULL,
            valor REAL NOT NULL,
            descricao TEXT,
            quilometragem INTEGER,
            cor TEXT,
            combustivel TEXT,
            cambio TEXT,
            status TEXT DEFAULT 'disponivel',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vehicle_photos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_id INTEGER NOT NULL,
            filename TEXT NOT NULL,
            ordem INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (vehicle_id) REFERENCES vehicles (id)
        )
    """)

    cursor.execute("SELECT * FROM users WHERE username = ?", ("admin",))
    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO users (username, password, name) VALUES (?, ?, ?)",
            ("admin", generate_password_hash("admin123"), "Administrador")
        )

    conn.commit()
    conn.close()

# ================= UTILIDADES =================

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated

# ================= ROTAS PÚBLICAS =================

@app.route("/")
def index():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT v.*, 
        (SELECT filename FROM vehicle_photos WHERE vehicle_id = v.id ORDER BY ordem LIMIT 1) AS foto_principal
        FROM vehicles v
        ORDER BY v.created_at DESC
    """)
    vehicles = cursor.fetchall()
    conn.close()

    return render_template("index.html", vehicles=vehicles)

@app.route("/veiculo/<int:id>")
def vehicle_details(id):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM vehicles WHERE id = ?", (id,))
    vehicle = cursor.fetchone()

    if not vehicle:
        conn.close()
        return redirect(url_for("index"))

    cursor.execute(
        "SELECT * FROM vehicle_photos WHERE vehicle_id = ? ORDER BY ordem", (id,)
    )
    photos = cursor.fetchall()
    conn.close()

    return render_template("vehicle_details.html", vehicle=vehicle, photos=photos)

# ================= LOGIN =================

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["name"] = user["name"]
            return redirect(url_for("admin_dashboard"))

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

# ================= ADMIN =================

@app.route("/admin")
@login_required
def admin_dashboard():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT v.*, 
        (SELECT filename FROM vehicle_photos WHERE vehicle_id = v.id ORDER BY ordem LIMIT 1) AS foto_principal
        FROM vehicles v
        ORDER BY v.created_at DESC
    """)
    vehicles = cursor.fetchall()
    conn.close()

    return render_template("admin_dashboard.html", vehicles=vehicles)

@app.route("/admin/veiculo/novo", methods=["GET", "POST"])
@login_required
def admin_new_vehicle():
    if request.method == "POST":
        data = (
            request.form.get("marca"),
            request.form.get("modelo"),
            request.form.get("ano"),
            request.form.get("valor"),
            request.form.get("descricao"),
            request.form.get("quilometragem"),
            request.form.get("cor"),
            request.form.get("combustivel"),
            request.form.get("cambio"),
            request.form.get("status", "disponivel"),
        )

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO vehicles
            (marca, modelo, ano, valor, descricao, quilometragem, cor, combustivel, cambio, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, data)

        vehicle_id = cursor.lastrowid

        files = request.files.getlist("photos")
        for i, file in enumerate(files):
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                name = f"{vehicle_id}_{i}_{filename}"
                path = os.path.join(app.config["UPLOAD_FOLDER"], name)
                file.save(path)

                cursor.execute(
                    "INSERT INTO vehicle_photos (vehicle_id, filename, ordem) VALUES (?, ?, ?)",
                    (vehicle_id, name, i),
                )

        conn.commit()
        conn.close()
        return redirect(url_for("admin_dashboard"))

    return render_template("admin_vehicle_form.html")

# ================= INIT =================

init_db()
