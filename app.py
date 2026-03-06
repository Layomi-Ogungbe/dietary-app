from flask import Flask, render_template, request, redirect, session, url_for, jsonify, Response, flash
import psycopg2
from psycopg2.extras import RealDictCursor
from flask_bcrypt import Bcrypt
from nutrition_calculation import calculate_targets
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import base64
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import random
import os
import webbrowser
from threading import Timer
import sys


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


app = Flask(
    __name__,
    template_folder=resource_path("templates"),
    static_folder=resource_path("static")
)

app.secret_key = "letsgofor1000%"
bcrypt = Bcrypt(app)


def get_db():
    return psycopg2.connect(
        os.getenv("DATABASE_URL"),
        cursor_factory=RealDictCursor
    )


#conn = psycopg2.connect("dbname=dietary_app user=layom host=localhost")
#print("connected!")

UPSERT_USER_PREFS = """
INSERT INTO user_preferences (
  user_id, calorie_target, protein_target_g, carbs_target_g, fat_target_g,
  sugar_target_g, fiber_target_g, sodium_target_mg, water_target_glasses,
  preferred_tags, disliked_tags, allergies
)
VALUES (
  %(user_id)s, %(calorie_target)s, %(protein_target_g)s, %(carbs_target_g)s, %(fat_target_g)s,
  %(sugar_target_g)s, %(fiber_target_g)s, %(sodium_target_mg)s, %(water_target_glasses)s,
  %(preferred_tags)s, %(disliked_tags)s, %(allergies)s
)
ON CONFLICT (user_id) DO UPDATE SET
  calorie_target = EXCLUDED.calorie_target,
  protein_target_g = EXCLUDED.protein_target_g,
  carbs_target_g = EXCLUDED.carbs_target_g,
  fat_target_g = EXCLUDED.fat_target_g,
  sugar_target_g = EXCLUDED.sugar_target_g,
  fiber_target_g = EXCLUDED.fiber_target_g,
  sodium_target_mg = EXCLUDED.sodium_target_mg,
  water_target_glasses = EXCLUDED.water_target_glasses,
  preferred_tags = EXCLUDED.preferred_tags,
  disliked_tags = EXCLUDED.disliked_tags,
  allergies = EXCLUDED.allergies;
"""

UPDATE_TARGETS_ONLY = """
UPDATE user_preferences
SET
  calorie_target = %(calorie_target)s,
  protein_target_g = %(protein_target_g)s,
  carbs_target_g = %(carbs_target_g)s,
  fat_target_g = %(fat_target_g)s,
  sugar_target_g = %(sugar_target_g)s,
  fiber_target_g = %(fiber_target_g)s,
  sodium_target_mg = %(sodium_target_mg)s,
  water_target_glasses = %(water_target_glasses)s
WHERE user_id = %(user_id)s;
"""


def london_today():
    return datetime.now(ZoneInfo("Europe/London")).date()


def ensure_daily_log(cur, user_id, log_date):
    cur.execute("""
        INSERT INTO user_daily_logs (user_id, log_date, calories, protein_g, carbs_g, fat_g, sugar_g, fiber_g, sodium_mg, water_glasses)
        VALUES (%s, %s, 0, 0, 0, 0, 0, 0, 0, 0)
        ON CONFLICT (user_id, log_date) DO NOTHING
    """, (user_id, log_date))


@app.route("/")
def index():
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db()
        cur = conn.cursor()

        cur.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cur.fetchone()
        cur.close()
        conn.close()

        if user is None:
            return render_template("login.html", error="User not found")

        if not bcrypt.check_password_hash(user["password_hash"], password):
            return render_template("login.html", error="Incorrect password")

        session["user_id"] = user["id"]

        return redirect(url_for("dashboard"))
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    conn = get_db()
    cur = conn.cursor()

    ensure_daily_log(cur, user_id, london_today())
    conn.commit()

    cur.execute("SELECT fullname FROM users WHERE id = %s", (user_id,))
    user = cur.fetchone()

    cur.execute("SELECT * FROM meals ")
    foods = cur.fetchall()

    cur.execute("SELECT calorie_target, protein_target_g, carbs_target_g, fat_target_g, sugar_target_g, fiber_target_g, sodium_target_mg, water_target_glasses, preferred_tags, disliked_tags, allergies FROM user_preferences WHERE user_id = %s", (user_id,))
    prefs = cur.fetchone()

    cur.execute("SELECT calories, carbs_g, fat_g, protein_g, sugar_g, fiber_g, sodium_mg, water_glasses FROM user_daily_logs WHERE user_id = %s AND log_date = %s", (user_id, london_today()))
    logs_today = cur.fetchone()

    cur.close()
    conn.close()

    pref_tags = set(prefs["preferred_tags"] or [])
    disliked_tags = set(prefs["disliked_tags"] or [])
    allergies = set(prefs["allergies"] or [])

    for food in foods:
        food["matches"] = 0
        food["conflicts"] = 0

        food_tags = set(food["tags"] or [])
        food_allergens = set(food["allergens"] or [])

        food["matches"] = len(food_tags & pref_tags)
        food["conflicts"] = len(food_tags & disliked_tags) + 2 * (len(food_allergens & allergies))

    foods.sort(key=lambda f: (-f["matches"], f["conflicts"]))
    foods = foods[:10]
    foods_pick3 = random.sample(foods, 3)

    return render_template(
        "dashboard.html",
        user=user,
        prefs=prefs,
        progress=logs_today,
        foods=foods_pick3
    )


@app.route("/menu", methods=["GET", "POST"])
def menu():
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM meals ORDER BY food_name")
    foods = cur.fetchall()

    cur.execute("SELECT calorie_target, preferred_tags, disliked_tags, allergies FROM user_preferences WHERE user_id = %s", (session["user_id"],))
    prefs = cur.fetchone()

    cur.close()
    conn.close()

    for food in foods:
        food["matches"] = 0
        food["conflicts"] = 0

        food_tags = set(food["tags"] or [])
        food_allergens = set(food["allergens"] or [])
        pref_tags = set(prefs["preferred_tags"] or [])
        disliked_tags = set(prefs["disliked_tags"] or [])
        allergies = set(prefs["allergies"] or [])

        food["matches"] = len(food_tags & pref_tags)
        food["conflicts"] = len(food_tags & disliked_tags) + 2 * (len(food_allergens & allergies))
        if len(food_allergens & allergies) > 0:
            food["allergy_warning"] = True
        else:
            food["allergy_warning"] = False

    foods.sort(key=lambda f: (-f["matches"], f["conflicts"]))
    return render_template("menu.html", foods=foods)


@app.route("/log_meal", methods=["POST"])
def log_meal():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]
    meal_id = request.form.get("meal_id")

    try:
        servings = float(request.form.get("servings", "1"))
    except ValueError:
        servings = 1.0

    if not meal_id or servings <= 0:
        return redirect(url_for("menu"))

    log_date = london_today()

    conn = get_db()
    cur = conn.cursor()

    try:
        ensure_daily_log(cur, user_id, log_date)

        cur.execute("SELECT * FROM meals WHERE id = %s", (meal_id,))
        meal = cur.fetchone()
        if not meal:
            conn.rollback()
            return redirect(url_for("menu"))

        def n(x):
            return float(x or 0)

        calories = n(meal.get("calories")) * servings
        protein_g = n(meal.get("protein_g")) * servings
        carbs_g = n(meal.get("carbs_g")) * servings
        fat_g = n(meal.get("fat_g")) * servings
        sugar_g = n(meal.get("sugar_g")) * servings
        fiber_g = n(meal.get("fiber_g")) * servings
        sodium_mg = n(meal.get("sodium_mg")) * servings

        cur.execute("""
            INSERT INTO user_meal_logs (
                user_id, meal_id, meal_name, servings, calories, protein_g, carbs_g, fat_g, sugar_g, fiber_g, sodium_mg, log_date
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
        """, (
            user_id, meal["id"], meal["food_name"], servings, calories, protein_g, carbs_g, fat_g, sugar_g, fiber_g, sodium_mg, log_date
        ))

        cur.execute("""
            UPDATE user_daily_logs
            SET calories  = calories  + %s,
                protein_g = protein_g + %s,
                carbs_g   = carbs_g   + %s,
                fat_g     = fat_g     + %s,
                sugar_g   = sugar_g   + %s,
                fiber_g   = fiber_g   + %s,
                sodium_mg = sodium_mg + %s
            WHERE user_id = %s AND log_date = %s
        """, (
            calories, protein_g, carbs_g, fat_g, sugar_g, fiber_g, sodium_mg, user_id, log_date
        ))

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        cur.close()
        conn.close()

    return redirect(url_for("menu"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        fullname = request.form["fullname"]
        email = request.form["email"]
        password = request.form["password"]

        password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

        conn = get_db()
        cur = conn.cursor()

        cur.execute("INSERT INTO users (fullname, email, password_hash) VALUES (%s, %s, %s) RETURNING id", (fullname, email, password_hash))

        user_id = cur.fetchone()["id"]
        conn.commit()
        cur.close()
        conn.close()

        session["user_id"] = user_id

        return redirect(url_for("setup_info"))

    return render_template("register.html")


@app.route("/setup-info", methods=["GET", "POST"])
def setup_info():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        age = request.form["age"]
        weight = request.form["weight"]
        height = request.form["height"]
        gender = request.form["gender"]
        activity = request.form["activity_level"]
        goal = request.form["dietary_goal"]

        conn = get_db()
        cur = conn.cursor()

        cur.execute("""
            UPDATE users
            SET age=%s, weight_kg=%s, height_cm=%s, gender=%s, activity_level=%s, dietary_goal=%s
            WHERE id=%s
        """, (age, weight, height, gender, activity, goal, session["user_id"]))

        profile = {
            "age": int(age),
            "weight_kg": float(weight),
            "height_cm": float(height),
            "gender": gender,
            "activity_level": activity,
            "dietary_goal": goal,
        }

        targets = calculate_targets(profile)

        prefs = {
            "user_id": session["user_id"],
            "preferred_tags": [],
            "disliked_tags": [],
            "allergies": [],
        }

        prefs.update(targets)

        cur.execute(UPSERT_USER_PREFS, prefs)

        conn.commit()
        cur.close()
        conn.close()

        return redirect(url_for("setup_preferences"))

    return render_template("registration_info.html")


@app.route("/setup-preferences", methods=["GET", "POST"])
def setup_preferences():
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()
    cur = conn.cursor()

    # Fetch user profile from users table
    cur.execute("""
        SELECT age, weight_kg, height_cm, gender, activity_level, dietary_goal
        FROM users
        WHERE id = %s
    """, (session["user_id"],))

    row = cur.fetchone()

    profile = {
        "age": row["age"],
        "weight_kg": float(row["weight_kg"]),
        "height_cm": float(row["height_cm"]),
        "gender": row["gender"],
        "activity_level": row["activity_level"],
        "dietary_goal": row["dietary_goal"],
    }

    if request.method == "POST":
        calorie_target = int(request.form["calorie_target"])

        preferred_tags = request.form.getlist("preferred_tags")
        disliked_tags = request.form.getlist("disliked_tags")
        allergies = request.form.getlist("allergens")

        targets = calculate_targets(profile, calorie_override=calorie_target)

        payload = {
            "user_id": session["user_id"],
            **targets,
            "preferred_tags": preferred_tags,
            "disliked_tags": disliked_tags,
            "allergies": allergies,
        }

        cur.execute(UPSERT_USER_PREFS, payload)
        conn.commit()

        cur.close()
        conn.close()
        return redirect(url_for("dashboard"))

    # GET: compute suggested calories to pre-fill the form
    targets = calculate_targets(profile)
    suggested_calories = targets["calorie_target"]

    cur.close()
    conn.close()
    return render_template(
        "preference_setup.html",
        suggested_calories=suggested_calories
    )


@app.route("/profile", methods=["GET"])
def profile():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            id,
            fullname,
            email,
            age,
            weight_kg,
            height_cm,
            gender,
            activity_level,
            dietary_goal,
            created_at
        FROM users
        WHERE id = %s
    """, (user_id,))
    user = cur.fetchone()

    # Preferences table
    cur.execute("""
        SELECT
            calorie_target,
            protein_target_g,
            carbs_target_g,
            fat_target_g,
            sugar_target_g,
            fiber_target_g,
            sodium_target_mg,
            water_target_glasses,
            preferred_tags,
            disliked_tags,
            allergies
        FROM user_preferences
        WHERE user_id = %s
    """, (user_id,))
    p = cur.fetchone()

    cur.close()
    conn.close()

    # Build "prefs" dict safely even if row doesn't exist yet
    prefs = p or {
        "calorie_target": 0,
        "preferred_tags": [],
        "disliked_tags": [],
        "allergies": []
    }

    all_tags = [
        "indian",
        "italian",
        "asian",
        "american",
        "japanese",
        "mexican",
        "middle-eastern",
        "british",
        "high-protein",
        "low-fat",
        "low-calorie",
        "high-sugar",
        "high-fiber",
        "healthy",
        "fried",
        "vegetarian",
        "spicy",
        "breakfast"
    ]

    allergens = ["Milk", "Egg", "Lupin", "Tree Nuts", "Gluten", "Soya", "Fish", "Molluscs", "Crustaceans", "Peanuts", "Sesame", "Sulphites", "Mustard", "Celery"]

    return render_template(
        "profile.html",
        user=user,
        prefs=prefs,
        all_tags=all_tags,
        allergens=allergens
    )


@app.route("/profile/edit-account", methods=["POST"])
def update_profile_account():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    fullname = request.form.get("fullname", "").strip()
    email = request.form.get("email", "").strip()

    age = int(request.form.get("age", "0"))
    weight = float(request.form.get("weight", "0"))
    height = float(request.form.get("height", "0"))

    activity = request.form.get("activity_level")
    goal = request.form.get("dietary_goal")

    gender = request.form.get("gender")

    conn = get_db()
    cur = conn.cursor()

    # Update users table
    cur.execute("""
        UPDATE users
        SET fullname=%s,
            email=%s,
            age=%s,
            gender=%s,
            weight_kg=%s,
            height_cm=%s,
            activity_level=%s,
            dietary_goal=%s
        WHERE id=%s
    """, (fullname, email, age, gender, weight, height, activity, goal, user_id))

    profile = {
        "age": age,
        "weight_kg": weight,
        "height_cm": height,
        "gender": gender,
        "activity_level": activity,
        "dietary_goal": goal,
    }

    targets = calculate_targets(profile)

    upd = {"user_id": user_id}
    upd.update(targets)
    cur.execute(UPDATE_TARGETS_ONLY, upd)

    conn.commit()
    cur.close()
    conn.close()

    return redirect(url_for("profile"))


@app.route("/profile/preferences", methods=["POST"])
def update_profile_preferences():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    calorie_target = int(request.form.get("calorie_target", "2000"))
    preferred_tags = request.form.getlist("preferred_tags")
    disliked_tags = request.form.getlist("disliked_tags")
    allergies = request.form.getlist("allergies")

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT age, weight_kg, height_cm, gender, activity_level, dietary_goal
        FROM users
        WHERE id=%s
    """, (user_id,))

    profile = cur.fetchone()

    targets = calculate_targets(profile, calorie_override=calorie_target)

    upd = {
        "user_id": user_id,
        "preferred_tags": preferred_tags,
        "disliked_tags": disliked_tags,
        "allergies": allergies,
    }

    upd.update(targets)

    cur.execute(UPSERT_USER_PREFS, upd)
    conn.commit()

    cur.close()
    conn.close()

    return redirect(url_for("profile"))


@app.route("/report/data", methods=["GET"])
def report_data():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]
    start_s = request.args.get("start")
    end_s = request.args.get("end")

    if not start_s or not end_s:
        return jsonify({"error": "Missing start or end date"}), 400

    # Parse + validate dates
    try:
        start_date = datetime.strptime(start_s, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_s, "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"error": "Invalid date format (use YYYY-MM-DD)"}), 400

    if end_date < start_date:
        return jsonify({"error": "End date must be on/after start date"}), 400

    conn = get_db()
    cur = conn.cursor()

    # Get User info
    cur.execute("""
        SELECT fullname, age, gender, weight_kg, height_cm
        FROM users
        WHERE id = %s
    """, (user_id,))
    u = cur.fetchone()
    if not u:
        cur.close()
        conn.close()
        return jsonify({"error": "User not found"}), 404

    #  Get targets
    cur.execute("""
        SELECT calorie_target, protein_target_g, carbs_target_g, fat_target_g, sugar_target_g, fiber_target_g, sodium_target_mg, water_target_glasses
        FROM user_preferences
        WHERE user_id = %s """, (user_id,))
    prefs = cur.fetchone() or {}

    # Get all logs in the date range
    cur.execute("""
        SELECT log_date,
               calories, protein_g, carbs_g, fat_g, sugar_g, fiber_g, sodium_mg, water_glasses
        FROM user_daily_logs
        WHERE user_id = %s AND log_date BETWEEN %s AND %s
        ORDER BY log_date
    """, (user_id, start_date, end_date))
    rows = cur.fetchall()

    cur.close()
    conn.close()

    # Build full date range (
    labels = []
    begdate = start_date
    while begdate <= end_date:
        labels.append(begdate.strftime("%Y-%m-%d"))
        begdate += timedelta(days=1)

    # Index logs by date string
    daily_logs = {r["log_date"].strftime("%Y-%m-%d"): r for r in rows}

    # build a series for a column across all days (missing days -> 0)
    def build_series(colname: str):
        out = []
        for date in labels:
            row = daily_logs.get(date)
            val = 0 if (not row or row[colname] is None) else row[colname]
            out.append(float(val))
        return out

    def avg_logged(colname: str):
        logged_vals = []
        for r in rows:
            val = r.get(colname)
            if val is not None:
                logged_vals.append(float(val))
        return round(sum(logged_vals) / len(logged_vals)) if logged_vals else 0

    actual = {
        "calories": build_series("calories"),
        "protein": build_series("protein_g"),
        "carbs": build_series("carbs_g"),
        "fat": build_series("fat_g"),
        "sugar": build_series("sugar_g"),
        "fibre": build_series("fiber_g"),
        "sodium": build_series("sodium_mg"),
        "water": build_series("water_glasses"),
    }

    match = {
        "calories": "calories",
        "protein": "protein_g",
        "carbs": "carbs_g",
        "fat": "fat_g",
        "sugar": "sugar_g",
        "fibre": "fiber_g",
        "sodium": "sodium_mg",
        "water": "water_glasses",
    }

    targets = {
        "calories": int(prefs.get("calorie_target") or 0),
        "protein": int(prefs.get("protein_target_g") or 0),
        "carbs": int(prefs.get("carbs_target_g") or 0),
        "fat": int(prefs.get("fat_target_g") or 0),
        "sugar": int(prefs.get("sugar_target_g") or 0),
        "fibre": int(prefs.get("fiber_target_g") or 0),
        "sodium": int(prefs.get("sodium_target_mg") or 0),
        "water": int(prefs.get("water_target_glasses") or 0),
    }

    def total(values):
        return round(sum(values)) if values else 0

    series = {}
    summary = {}

    for key, values in actual.items():
        mean = avg_logged(match[key])
        target = targets.get(key, 0)
        series[key] = {
            "actual": values,
            "avg": [mean] * len(labels),
            "target": [target] * len(labels)
        }
        summary[key] = {"total": total(values), "avg": mean, "target": target}

    return jsonify({
        "user": {
            "name": u["fullname"],
            "age": u["age"],
            "gender": u["gender"],
            "weight": float(u["weight_kg"] or 0),
            "height": float(u["height_cm"] or 0),
        },
        "labels": labels,
        "series": series,
        "summary": summary
    })


def _data_url_to_png_bytes(data_url: str) -> bytes:
    if not data_url or "," not in data_url:
        raise ValueError("Invalid image data URL")
    _, b64 = data_url.split(",", 1)
    return base64.b64decode(b64)


@app.route("/report/pdf", methods=["POST"])
def report_pdf():
    if "user_id" not in session:
        return Response("Not logged in", status=401)

    payload = request.get_json(silent=True) or {}
    user = payload.get("user", {})
    range_ = payload.get("range", {})
    summary = payload.get("summary", {})
    charts = payload.get("charts", {})

    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    w, h = A4

    # ---- Header ----
    c.setFont("Helvetica-Bold", 18)
    c.drawString(40, h - 50, "Dietary Report")

    c.setFont("Helvetica", 10)
    c.drawString(40, h - 70, f"Date range: {range_.get('start','')} to {range_.get('end','')}")
    c.drawString(40, h - 85, f"Name: {user.get('name','')}")
    c.drawString(40, h - 100, f"Age: {user.get('age','')}   Gender: {user.get('gender','')}")
    c.drawString(40, h - 115, f"Weight: {user.get('weight','')} kg   Height: {user.get('height','')} cm")

    y = h - 145

    # ---- Summary table ----
    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, y, "Summary")
    y -= 18

    c.setFont("Helvetica-Bold", 10)
    c.drawString(40, y, "Nutrient")
    c.drawRightString(270, y, "Total")
    c.drawRightString(350, y, "Avg/day")
    c.drawString(380, y, "Reference")
    y -= 14

    order = ["calories", "protein", "carbs", "fat", "sugar", "fibre", "sodium", "water"]
    units = {"calories": "kcal", "protein": "g", "carbs": "g", "fat": "g", "sugar": "g", "fibre": "g", "sodium": "mg", "water": "glasses"}
    c.setFont("Helvetica", 10)

    for key in order:
        info = summary.get(key)
        if not info:
            continue

        label = str(info.get("label", key)) + " (" + units[key] + ")"
        total = str(info.get("total", ""))
        avg_ = str(info.get("avg", ""))
        target = str(info.get("target", ""))
        typ = info.get("type", "tgt")

        ref_label = "Target"
        if typ == "lmt":
            ref_label = "Limit"
        elif typ == "min":
            ref_label = "Minimum"

        c.drawString(40, y, label)
        c.drawRightString(270, y, total)
        c.drawRightString(350, y, avg_)
        c.drawString(380, y, f"{ref_label}: {target}")
        y -= 14

        if y < 160:
            c.showPage()
            y = h - 50

    # ---- Charts (2 per row, side-by-side) ----
    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, y - 10, "Charts")
    y -= 30

    left_margin = 40
    right_margin = 40
    gap = 15  # gap between the two charts

    usable_w = w - left_margin - right_margin
    col_w = (usable_w - gap) / 2

    chart_h = 180
    title_h = 12
    block_h = title_h + 8 + chart_h + 18  # total vertical space per chart "block"

    col = 0  # 0=left, 1=right

    for key in order:
        data_url = charts.get(key)
        if not data_url:
            continue

        try:
            img_bytes = _data_url_to_png_bytes(data_url)
            img = ImageReader(BytesIO(img_bytes))
        except Exception:
            continue

        # If we're too low for another row, go to next page
        if y < 80 + block_h:
            c.showPage()
            y = h - 50
            c.setFont("Helvetica-Bold", 12)
            c.drawString(40, y - 10, "Charts (cont.)")
            y -= 30
            col = 0

        x = left_margin + col * (col_w + gap)

        # Title
        c.setFont("Helvetica-Bold", 10)
        c.drawString(x, y, str(summary.get(key, {}).get("label", key)).capitalize())

        # Image
        img_y_top = y - 8
        c.drawImage(
            img,
            x,
            img_y_top - chart_h,
            width=225,
            height=chart_h,
            preserveAspectRatio=False,
            anchor="sw",
        )

        # Move to next column; if we just placed right column, drop to next row
        if col == 0:
            col = 1
        else:
            col = 0
            y -= block_h

    c.save()
    buf.seek(0)

    return Response(
        buf.getvalue(),
        mimetype="application/pdf",
        headers={"Content-Disposition": "attachment; filename=dietary-report.pdf"},
    )


@app.route("/log-water", methods=["POST"])
def log_water():
    if "user_id" not in session:
        return jsonify({"error": "not logged in"}), 401

    data = request.get_json(silent=True) or {}
    amount = int(data.get("amount", 0))

    user_id = session["user_id"]

    conn = get_db()
    cur = conn.cursor()

    # ensure today's row exists
    ensure_daily_log(cur, user_id, london_today())

    # get target so we can cap the value
    cur.execute("SELECT water_target_glasses FROM user_preferences WHERE user_id=%s", (user_id,))
    pref = cur.fetchone() or {}
    target = int(pref.get("water_target_glasses") or 8)

    # update
    cur.execute("""
        UPDATE user_daily_logs
        SET water_glasses = GREATEST(0, LEAST(%s, water_glasses + %s))
        WHERE user_id=%s AND log_date=%s
        RETURNING water_glasses
    """, (target, amount, user_id, london_today()))

    row = cur.fetchone()
    water = int(row["water_glasses"]) if row else 0

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"water": water, "target": target})


@app.route("/log_custom_meals", methods=["POST"])
def log_custom_meals():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]
    log_date = london_today()

    #Just for safe handling
    def secParse(name, default=0.0):
        try:
            return float(request.form.get(name, default) or default)
        except (TypeError, ValueError):
            return float(default)

    meal_name = (request.form.get("meal_name") or "").strip()

    servings = secParse("servings", 1.0)
    if servings <= 0:
        return redirect(url_for("menu"))

    calories = secParse("calories", 0) * servings
    protein_g = secParse("protein_g", 0) * servings
    carbs_g = secParse("carbs_g", 0) * servings
    fat_g = secParse("fat_g", 0) * servings
    sugar_g = secParse("sugar_g", 0) * servings
    fiber_g = secParse("fiber_g", 0) * servings
    sodium_mg = secParse("sodium_mg", 0) * servings

    conn = get_db()
    cur = conn.cursor()

    try:
        ensure_daily_log(cur, user_id, log_date)

        cur.execute("""
            UPDATE user_daily_logs
            SET calories = calories + %s,
                protein_g = protein_g + %s,
                carbs_g = carbs_g + %s,
                fat_g = fat_g + %s,
                sugar_g = sugar_g + %s,
                fiber_g = fiber_g + %s,
                sodium_mg = sodium_mg + %s
            WHERE user_id = %s AND log_date = %s
        """, (
            calories, protein_g, carbs_g, fat_g, sugar_g, fiber_g, sodium_mg, user_id, log_date
        ))

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        cur.close()
        conn.close()

    return redirect(url_for("menu"))


@app.route("/profile/change-password", methods=["POST"])
def change_password():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    current_password = request.form.get("current_password", "")
    new_password = request.form.get("new_password", "")
    confirm_password = request.form.get("confirm_password", "")


    if not current_password or not new_password or not confirm_password:
        flash("Please fill all fields", 'error')
        return redirect(url_for("profile"))

    if new_password != confirm_password:
        flash("Passwords don't match", 'error')
        return redirect(url_for("profile"))

    if len(new_password) < 8:
        flash("Password is too short (8 chr min)", 'error')
        return redirect(url_for("profile"))

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT password_hash FROM users WHERE id = %s", (user_id,))
    user = cur.fetchone()

    if not user:
        cur.close()
        conn.close()
        return redirect(url_for("profile"))

    if not bcrypt.check_password_hash(user["password_hash"], current_password):
        cur.close()
        conn.close()
        flash("Wrong Password", 'error')
        return redirect(url_for("profile"))

    new_password_hash = bcrypt.generate_password_hash(new_password).decode("utf-8")

    cur.execute("""
        UPDATE users
        SET password_hash = %s
        WHERE id = %s
    """, (new_password_hash, user_id))

    conn.commit()
    cur.close()
    conn.close()

    flash("Password changed", 'success')
    return redirect(url_for("profile"))


def open_browser():
    webbrowser.open("http://127.0.0.1:5000")


if __name__ == "__main__":
	app.run(host="0.0.0.0", port=10000, debug=False)
