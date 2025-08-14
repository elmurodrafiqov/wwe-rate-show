from flask import Flask, render_template, request, redirect, url_for, session
import json
import os
from datetime import datetime

app = Flask(name)
app.secret_key = "super_secret_key"  # Sessiya uchun maxfiy kalit

# Admin ma'lumotlari
ADMIN_USERNAME = "elmur"
ADMIN_PASSWORD = "elmurodmacho"

DATA_FILE = "data/ratings.json"

# Agar data papkasi yo'q bo'lsa, yaratamiz
os.makedirs("data", exist_ok=True)

# Agar fayl bo'sh bo'lsa, boshlang'ich ma'lumotlar bilan yaratamiz
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({
            "show_name": "SmackDown",
            "show_date": datetime.now().strftime("%Y-%m-%d"),
            "ratings": [],
            "voting_open": True
        }, f)


def load_data():
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)


@app.route("/", methods=["GET", "POST"])
def index():
    data = load_data()
    if request.method == "POST":
        if not data["voting_open"]:
            return "Voting is closed!"
        try:
            rating = float(request.form["rating"])
        except:
            return "Invalid rating!"

        if rating < 0 or rating > 10:
            return "Rating must be between 0 and 10!"

        data["ratings"].append(rating)
        save_data(data)
        return redirect(url_for("thank_you"))

    return render_template("index.html", show_name=data["show_name"], show_date=data["show_date"], voting_open=data["voting_open"])


@app.route("/thank_you")
def thank_you():
    return "Thank you for voting!"


@app.route("/admin", methods=["GET", "POST"])
def admin():
    if "logged_in" not in session:
        return redirect(url_for("login"))

    data = load_data()
    avg_rating = round(sum(data["ratings"]) / len(data["ratings"]), 2) if data["ratings"] else 0

    if request.method == "POST":
        if "update_show" in request.form:
            data["show_name"] = request.form["show_name"]
            data["show_date"] = request.form["show_date"]
        elif "toggle_voting" in request.form:
            data["voting_open"] = not data["voting_open"]

        save_data(data)
        return redirect(url_for("admin"))

    return render_template("admin.html", data=data, avg_rating=avg_rating)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session["logged_in"] = True
            return redirect(url_for("admin"))
        else:
            return "Invalid credentials!"

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("logged_in", None)
    return redirect(url_for("login"))


if name == "main":
    app.run(debug=True)