from flask import Flask, render_template, request, redirect, url_for, session, abort
import json, os
from datetime import datetime

# === Config ===
BASE_DIR = os.path.dirname(os.path.abspath(file))
DATA_DIR = os.path.join(BASE_DIR, "data")
DATA_FILE = os.path.join(DATA_DIR, "ratings.json")

# Admin kirish ma'lumotlari
ADMIN_USERNAME = "elmur"
ADMIN_PASSWORD = "elmurodmacho"

# Flask app
app = Flask(__name__)
# Productionda ENV orqali berib qo'yish mumkin: SECRET_KEY
app.secret_key = os.environ.get("SECRET_KEY", "change-this-dev-secret-key")

# === Storage helpers ===
def ensure_storage():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(DATA_FILE):
        initial = {
            "show_name": "SmackDown",
            "show_date": datetime.now().strftime("%Y-%m-%d"),  # ISO format
            "voting_open": True,
            "ratings": []  # list of dicts: {user, score, time}
        }
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(initial, f, indent=4, ensure_ascii=False)

def load_data():
    ensure_storage()
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# === Routes ===
@app.route("/", methods=["GET", "POST"])
def index():
    data = load_data()

    if request.method == "POST":
        if not data.get("voting_open", False):
            return "Voting is closed!", 403

        # Kim baho berganini admin ko'ra olishi uchun nickname majburiy
        username = (request.form.get("username") or "").strip()
        raw_score = (request.form.get("rating") or "").strip()

        if not username:
            return "Please enter your name!", 400

        try:
            score = float(raw_score)
        except:
            return "Invalid rating!", 400

        if score < 0 or score > 10:
            return "Rating must be between 0 and 10!", 400

        data["ratings"].append({
            "user": username,
            "score": round(score, 2),
            "time": datetime.utcnow().isoformat() + "Z"
        })
        save_data(data)
        return redirect(url_for("thank_you"))

    return render_template(
        "index.html",
        show_name=data.get("show_name", ""),
        show_date=data.get("show_date", ""),
        voting_open=data.get("voting_open", False)
    )

@app.route("/thank_you")
def thank_you():
    return "Thank you for voting!"

# --- Admin auth ---
def require_admin():
    if not session.get("admin", False):
        return False
    return True

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u = request.form.get("username", "")
        p = request.form.get("password", "")
        if u == ADMIN_USERNAME and p == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect(url_for("admin_panel"))
        return "Invalid credentials!", 403
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("admin", None)
    return redirect(url_for("login"))

# --- Admin panel ---
@app.route("/admin", methods=["GET", "POST"])
def admin_panel():
    if not require_admin():
        return redirect(url_for("login"))

    data = load_data()

    if request.method == "POST":
        action = request.form.get("action")

        if action == "update_show":
            data["show_name"] = request.form.get("show_name", data["show_name"]).strip()
            data["show_date"] = request.form.get("show_date", data["show_date"]).strip()
            save_data(data)
            return redirect(url_for("admin_panel"))

        elif action == "toggle_voting":
            data["voting_open"] = not data.get("voting_open", True)
            save_data(data)
            return redirect(url_for("admin_panel"))

        elif action == "clear_ratings":
            data["ratings"] = []
            save_data(data)
            return redirect(url_for("admin_panel"))else:
            abort(400, "Unknown action")

    ratings = data.get("ratings", [])
    avg = round(sum(r["score"] for r in ratings) / len(ratings), 2) if ratings else 0.0

    return render_template("admin.html", data=data, avg_rating=avg, ratings=ratings)

# (ixtiyoriy) favicon 404 chiqmasligi uchun
@app.route("/favicon.ico")
def favicon():
    return ("", 204)

# Lokal ishga tushirish uchun
if name == "main":
    # Render’da gunicorn ishga tushiradi; quyi qator faqat lokal uchun
    app.run(host="0.0.0.0", port=5000, debug=True)