from flask import Flask, render_template, request, redirect, url_for, session, abort
import json
import os

app = Flask(__name__)
app.secret_key = "supersecretkey"

# Admin login ma'lumotlari
ADMIN_USERNAME = "elmur"
ADMIN_PASSWORD = "elmurodmacho"

DATA_FILE = "data.json"

# JSON faylni yuklash
def load_data():
    if not os.path.exists(DATA_FILE):
        return {"shows": [], "ratings": []}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

# JSON faylga saqlash
def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# Bosh sahifa - Reyting berish
@app.route("/", methods=["GET", "POST"])
def index():
    data = load_data()
    if request.method == "POST":
        show_name = request.form.get("show_name", "").strip()
        rating = request.form.get("rating", "").strip()
        
        if not show_name or not rating:
            abort(400, "Show name va rating to‘ldirilishi kerak")
        
        try:
            rating = int(rating)
            if rating < 1 or rating > 10:
                abort(400, "Rating 1-10 orasida bo‘lishi kerak")
        except ValueError:
            abort(400, "Rating butun son bo‘lishi kerak")

        data["ratings"].append({"show": show_name, "rating": rating})
        save_data(data)
        return redirect(url_for("index"))

    return render_template("index.html", shows=data["shows"], ratings=data["ratings"])

# Admin login sahifasi
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect(url_for("admin_panel"))
        else:
            return render_template("login.html", error="Noto‘g‘ri login yoki parol")
    return render_template("login.html")

# Admin panel
@app.route("/admin", methods=["GET", "POST"])
def admin_panel():
    if not session.get("admin"):
        return redirect(url_for("login"))
    
    data = load_data()

    if request.method == "POST":
        action = request.form.get("action", "")
        
        if action == "add_show":
            show_name = request.form.get("show_name", "").strip()
            if show_name and show_name not in data["shows"]:
                data["shows"].append(show_name)
                save_data(data)
        
        elif action == "delete_show":
            show_name = request.form.get("show_name", "").strip()
            if show_name in data["shows"]:
                data["shows"].remove(show_name)
                data["ratings"] = [r for r in data["ratings"] if r["show"] != show_name]
                save_data(data)

    return render_template("admin.html", shows=data["shows"], ratings=data["ratings"])

# Logout
@app.route("/logout")
def logout():
    session.pop("admin", None)
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)