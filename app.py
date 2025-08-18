from flask import Flask, render_template, request, redirect, url_for, session
import json
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "supersecretkey"

DATA_FILE = "data/ratings.json"

# Fayl mavjud bo‘lmasa — yaratamiz
os.makedirs("data", exist_ok=True)
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({"show_name": "", "show_date": "", "ratings": []}, f)

# Admin login ma’lumotlari
ADMIN_USERNAME = "elmur"
ADMIN_PASSWORD = "elmurodmacho"

# Ma’lumotni o‘qish
def load_data():
    with open(DATA_FILE, "r") as f:
        return json.load(f)

# Ma’lumotni yozish
def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# Home sahifa
@app.route("/")
def home():
    data = load_data()
    return render_template("home.html", data=data)

# Reyting berish
@app.route("/rate", methods=["POST"])
def rate():
    data = load_data()

    rating = request.form.get("rating")
    if not rating or rating.strip() == "":
        return "Rating kiritilmadi!", 400

    try:
        rating = float(rating)
    except ValueError:
        return "Rating faqat raqam bo‘lishi kerak!", 400

    if rating < 0 or rating > 10:
        return "Rating 0 va 10 oralig‘ida bo‘lishi kerak!", 400

    data["ratings"].append({
        "value": rating,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    save_data(data)

    return redirect(url_for("home"))

# Login sahifa
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect(url_for("admin"))
        else:
            return "Login yoki parol noto‘g‘ri!"
    return render_template("login.html")

# Admin panel
@app.route("/admin", methods=["GET", "POST"])
def admin():
    if not session.get("admin"):
        return redirect(url_for("login"))

    data = load_data()

    if request.method == "POST":
        show_name = request.form.get("show_name")
        show_date = request.form.get("show_date")

        if show_name:
            data["show_name"] = show_name
        if show_date:
            data["show_date"] = show_date

        save_data(data)
        return redirect(url_for("admin"))

    avg_rating = round(sum(r["value"] for r in data["ratings"]) / len(data["ratings"]), 2) if data["ratings"] else 0
    return render_template("admin.html", data=data, avg_rating=avg_rating)

# Logout
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

if __name__ == "__main__":
    app.run(debug=True)