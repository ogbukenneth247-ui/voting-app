from flask import Flask, render_template, request, redirect, session, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import sqlite3
import random
import os

# --------------------
# APP CONFIG
# --------------------
app = Flask(__name__)

# Secret key (Render will use env var, local uses fallback)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key")

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

# --------------------
# ADMIN CREDENTIALS
# --------------------
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD_HASH = generate_password_hash("admin123")

# # --------------------
# DATABASE
# --------------------
def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS voters (
            voter_id TEXT PRIMARY KEY,
            name TEXT,
            year_of_birth INTEGER
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS votes (
            voter_id TEXT UNIQUE,
            candidate TEXT
        )
    """)

    conn.commit()
    conn.close()

# --------------------
# AUTH HELPERS
# --------------------
def is_logged_in():
    return "user" in session

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

# --------------------
# HOME
# --------------------
@app.route("/")
def home():
    if "user" in session:
        return render_template("dashboard.html")
    if "voter" in session:
        return redirect(url_for("voter_dashboard"))
    return redirect(url_for("voter_login"))

# --------------------
# ADMIN LOGIN
# --------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if (
            request.form["username"] == ADMIN_USERNAME
            and check_password_hash(ADMIN_PASSWORD_HASH, request.form["password"])
        ):
            session["user"] = ADMIN_USERNAME
            return redirect(url_for("home"))
        return render_template("login.html", error="Invalid login")

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# --------------------
# VOTER LOGIN
# --------------------
@app.route("/voter_login", methods=["GET", "POST"])
def voter_login():
    if request.method == "POST":
        voter_id = request.form["voter_id"]

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM voters WHERE voter_id = ?", (voter_id,))
        voter = cursor.fetchone()
        conn.close()

        if voter:
            session["voter"] = voter_id
            return redirect(url_for("voter_dashboard"))

        return render_template("voter_login.html", error="Invalid Voter ID")

    return render_template("voter_login.html")

@app.route("/voter_logout")
def voter_logout():
    session.pop("voter", None)
    return redirect(url_for("voter_login"))

# --------------------
# VOTER DASHBOARD
# --------------------
@app.route("/voter_dashboard")
def voter_dashboard():
    if "voter" not in session:
        return redirect(url_for("voter_login"))

    voter_id = session["voter"]

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM voters WHERE voter_id = ?", (voter_id,))
    voter = cursor.fetchone()

    cursor.execute("SELECT * FROM votes WHERE voter_id = ?", (voter_id,))
    voted = cursor.fetchone()

    conn.close()

    return render_template(
        "voter_dashboard.html",
        voter=voter,
        voted=bool(voted)
    )

# --------------------
# REGISTER VOTER (ADMIN)
# --------------------
@app.route("/register_voter", methods=["GET", "POST"])
@admin_required
def register_voter():
    if request.method == "POST":
        name = request.form["name"]
        year = request.form["year"]
        voter_id = "VOTE" + str(random.randint(1000, 9999))

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO voters (voter_id, name, year_of_birth) VALUES (?, ?, ?)",
            (voter_id, name, year)
        )
        conn.commit()
        conn.close()

        return render_template("register_voter.html", success=voter_id)

    return render_template("register_voter.html")

# --------------------
# VOTING
# --------------------
@app.route("/vote", methods=["GET", "POST"])
def vote():
    if "voter" not in session:
        return redirect(url_for("voter_login"))

    voter_id = session["voter"]

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM votes WHERE voter_id = ?", (voter_id,))
    if cursor.fetchone():
        conn.close()
        return render_template("vote.html", error="You have already voted")

    if request.method == "POST":
        candidate = request.form["candidate"]

        cursor.execute(
            "INSERT INTO votes (voter_id, candidate) VALUES (?, ?)",
            (voter_id, candidate)
        )
        conn.commit()
        conn.close()

        return render_template("vote.html", success="Vote submitted successfully")

    conn.close()
    return render_template("vote.html")

# --------------------
# RESULTS (ADMIN)
# --------------------
@app.route("/results")
@admin_required
def results():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT candidate, COUNT(*) as total
        FROM votes
        GROUP BY candidate
    """)
    results = cursor.fetchall()
    conn.close()

    return render_template("results.html", results=results)

# --------------------
# RUN
# --------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)




