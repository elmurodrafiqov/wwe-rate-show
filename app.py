import os
import json
import hashlib
from datetime import datetime
from functools import wraps
from flask import (
    Flask, render_template, request, redirect, url_for, session, abort,
    flash, send_file, make_response
)

# === Konfiguratsiya ===
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", os.urandom(24))
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin777")  # Render’da Env Vars-ga qo'ying
IP_SALT = os.getenv("IP_SALT", "rate_show_salt")          # IP hash uchun tuz
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
SETTINGS_PATH = os.path.join(DATA_DIR, "settings.json")
RATINGS_PATH = os.path.join(DATA_DIR, "ratings.json")

os.makedirs(DATA_DIR, exist_ok=True)

# === Yordamchi funksiyalar ===

def load_json(path, default):
    if not os.path.exists(path):
        save_json(path, default)
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_settings():
    default = {
        "show_name": "WWE Raw",
        "show_date": datetime.utcnow().strftime("%Y-%m-%d"),
        "header_image": "",
        "voting_open": True,
        "min_rating": 0.0,
        "max_rating": 10.0,
        "allow_decimals": True,
    }
    return load_json(SETTINGS_PATH, default)


def save_settings(s):
    save_json(SETTINGS_PATH, s)


def get_all_ratings():
    return load_json(RATINGS_PATH, {"shows": {}})


def save_all_ratings(r):
    save_json(RATINGS_PATH, r)


def show_key(settings=None):
    s = settings or get_settings()
    return f"{s['show_name'].strip()}::{s['show_date'].strip()}"


def hash_user(request):
    ip = request.headers.get("X-Forwarded-For", request.remote_addr) or "0.0.0.0"
    raw = f"{IP_SALT}|{ip}"
    return hashlib.sha256(raw.encode()).hexdigest()


def compute_stats(values):
    if not values:
        return {"count": 0, "avg": 0, "min": 0, "max": 0}
    count = len(values)
    avg = round(sum(values)/count, 3)
    return {"count": count, "avg": avg, "min": min(values), "max": max(values)}


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("is_admin"):
            return redirect(url_for("admin_login", next=request.path))
        return f(*args, **kwargs)
    return wrapper


# === Marshrutlar ===
@app.route("/")
def index():
    s = get_settings()
    key = show_key(s)
    data = get_all_ratings()
    show_data = data["shows"].get(key, {"ratings": []})

    # Foydalanuvchining oldin ovoz bergan-bermaganini tekshirish
    uid = hash_user(request)
    user_voted = any(r.get("user_id") == uid for r in show_data["ratings"])

    stats = compute_stats([r["value"] for r in show_data["ratings"]])

    return render_template(
        "index.html",
        settings=s,
        stats=stats,
        voting_open=s.get("voting_open", True),
        user_voted=user_voted
    )


@app.route("/rate", methods=["POST"])
def rate():
    s = get_settings()
    if not s.get("voting_open", True):
        flash("Ovoz berish yopilgan.", "warning")
        return redirect(url_for("index"))

    try:
        rating_str = request.form.get("rating", "").strip()
        name = (request.form.get("name", "").strip() or "")[:40]
        if rating_str == "":
            raise ValueError("rating empty")
        value = float(rating_str)
    except Exception:
        flash("Noto'g'ri baho. Masalan: 7.1", "danger")
        return redirect(url_for("index"))

    # Limitlar
    min_r = float(s.get("min_rating", 0))
    max_r = float(s.get("max_rating", 10))
    if not (min_r <= value <= max_r):
        flash(f"Baho {min_r}–{max_r} oralig'ida bo'lishi kerak.", "danger")
        return redirect(url_for("index"))

    uid = hash_user(request)
    key = show_key(s)
    data = get_all_ratings()
    show_data = data["shows"].setdefault(key, {"ratings": []})

    # Bitta foydalanuvchi — bitta ovoz
    if any(r.get("user_id") == uid for r in show_data["ratings"]):
        flash("Siz allaqachon ovoz bergansiz.", "info")
        return redirect(url_for("index"))

    show_data["ratings"].append({
        "user_id": uid,
        "name": name,
        "value": value,
        "timestamp": datetime.utcnow().isoformat(timespec="seconds") + "Z"
    })
    save_all_ratings(data)

    flash("Ovozingiz qabul qilindi!", "success")
    return redirect(url_for("index"))


# === Admin autentifikatsiya ===
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        pw = request.form.get("password", "")
        if pw == ADMIN_PASSWORD:
            session["is_admin"] = True
            flash("Admin sifatida kirdingiz.", "success")
            next_url = request.args.get("next") or url_for("admin")
            return redirect(next_url)
        flash("Parol noto'g'ri.", "danger")
    return render_template("admin.html", view="login")


@app.route("/admin/logout")
def admin_logout():
    session.pop("is_admin", None)
    flash("Chiqildi.", "info")
    return redirect(url_for("index"))


# === Admin panel ===
@app.route("/admin")
@login_required
def admin():
    s = get_settings()
    key = show_key(s)
    data = get_all_ratings()
    show_data = data["shows"].get(key, {"ratings": []})
    ratings = show_data["ratings"]

    # Statistikalar
    values = [r["value"] for r in ratings]
    stats = compute_stats(values)

    # Foydalanuvchini maskalash (hashning so'ngi 6 belgisi)
    for r in ratings:
        r["user_mask"] = r["user_id"][-6:]

    return render_template(
        "admin.html",
        view="dashboard",
        settings=s,
        ratings=sorted(ratings, key=lambda x: x["timestamp"], reverse=True),
        stats=stats,
        show_key=key
    )


@app.route("/admin/update-settings", methods=["POST"])
@login_required
def admin_update_settings():
    s = get_settings()
    s["show_name"] = (request.form.get("show_name", s["show_name"]).strip() or s["show_name"])[:80]
    s["show_date"] = (request.form.get("show_date", s["show_date"]).strip() or s["show_date"])[:10]
    s["header_image"] = request.form.get("header_image", s.get("header_image", "")).strip()
    s["voting_open"] = request.form.get("voting_open") == "on"

    try:
        s["min_rating"] = float(request.form.get("min_rating", s.get("min_rating", 0)))
        s["max_rating"] = float(request.form.get("max_rating", s.get("max_rating", 10)))
    except Exception:
        pass

    save_settings(s)
    flash("Sozlamalar saqlandi.", "success")
    return redirect(url_for("admin"))


@app.route("/admin/clear-current", methods=["POST"])
@login_required
def admin_clear_current():
    s = get_settings()
    key = show_key(s)
    data = get_all_ratings()
    if key in data["shows"]:
        data["shows"][key] = {"ratings": []}
        save_all_ratings(data)
    flash("Joriy shou reytinglari tozalandi.", "warning")
    return redirect(url_for("admin"))


@app.route("/admin/export.csv")
@login_required
def admin_export_csv():
    s = get_settings()
    key = show_key(s)
    data = get_all_ratings()
    ratings = data["shows"].get(key, {"ratings": []})["ratings"]

    # CSV tayyorlash
    lines = ["user_mask,name,value,timestamp"]
    for r in ratings:
        mask = r["user_id"][-6:]
        name = (r.get("name") or "").replace(",", " ")
        lines.append(f"{mask},{name},{r['value']},{r['timestamp']}")

    csv_data = "\n".join(lines)
    response = make_response(csv_data)
    response.headers["Content-Type"] = "text/csv"
    response.headers["Content-Disposition"] = f"attachment; filename=ratings_{key.replace('::','_')}.csv"
    return response


# === Lokal ishga tushirish ===
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)