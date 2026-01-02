from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
import random

app = Flask(__name__)
app.secret_key = "secret123"

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

def get_db():
    return sqlite3.connect("database.db")

def is_logged_in():
    return "user" in session

@app.route("/")
def home():
    if "user" in session:
        return render_template("dashboard.html")
    if "voter" in session:
        return redirect(url_for("voter_dashboard"))
    return redirect(url_for("voter_login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form["username"] == ADMIN_USERNAME and request.form["password"] == ADMIN_PASSWORD:
            session["user"] = ADMIN_USERNAME
            return redirect(url_for("home"))
        return render_template("login.html", error="Invalid login")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

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
        else:
            return render_template("voter_login.html", error="Invalid Voter ID")

    return render_template("voter_login.html")
@app.route("/voter_logout")
def voter_logout():
    session.pop("voter", None)
    return redirect(url_for("voter_login"))



# 👤 REGISTER VOTER
@app.route("/register_voter", methods=["GET", "POST"])
def register_voter():
    if not is_logged_in():
        return redirect(url_for("login"))

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

# 🗳️ VOTING
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
    conn.close()


    if request.method == "POST":
        candidate = request.form["candidate"]

        conn = get_db()
        cursor = conn.cursor()

        # check if already voted
        cursor.execute("SELECT * FROM votes WHERE voter_id = ?", (voter_id,))
        if cursor.fetchone():
            conn.close()
            return render_template("vote.html", error="You have already voted")

        cursor.execute(
            "INSERT INTO votes (voter_id, candidate) VALUES (?, ?)",
            (voter_id, candidate)
        )

        conn.commit()
        conn.close()

        return render_template("vote.html", success="Vote submitted successfully")

    return render_template("vote.html")


# 📊 RESULTS
@app.route("/results")
def results():
    if not is_logged_in():
        return redirect(url_for("login"))

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT candidate, COUNT(*) 
        FROM votes 
        GROUP BY candidate
    """)

    results = cursor.fetchall()
    conn.close()

    return render_template("results.html", results=results)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)




