from flask import Flask, render_template, request, redirect, session
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "secret123"

# Home
@app.route("/")
def home():
    return render_template("index.html")

# Register
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
            (name, email, password)
        )

        conn.commit()
        conn.close()

        return redirect("/login")

    return render_template("register.html")

# Login
# AI Subscription Advisor
@app.route("/ai_advisor")
def ai_advisor():
    if "user_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM subscriptions WHERE user_id=?",
        (session["user_id"],)
    )

    subscriptions = cursor.fetchall()
    conn.close()

    total_monthly = 0

    for sub in subscriptions:
        price = float(sub[4])
        billing_cycle = sub[5]

        if billing_cycle == "Monthly":
            total_monthly += price
        elif billing_cycle == "Yearly":
            total_monthly += price / 12

    if total_monthly == 0:
        recommendation = "No subscriptions found."
    elif total_monthly < 25:
        recommendation = "Your spending is low. Keep monitoring subscriptions."
    elif total_monthly <= 75:
        recommendation = "Your spending is moderate. Consider reviewing unused subscriptions."
    else:
        recommendation = "Your spending is high. Try cancelling unused subscriptions."

    return render_template(
        "ai_advisor.html",
        total_monthly=total_monthly,
        recommendation=recommendation
    )
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE email=? AND password=?",
            (email, password)
        )

        user = cursor.fetchone()
        conn.close()

        if user:
            session["user_id"] = user[0]
            return redirect("/dashboard")
        else:
            return "Invalid email or password"

    return render_template("login.html")

# Dashboard
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/login")

    search = request.args.get("search", "")
    sort_by = request.args.get("sort_by", "")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    query = "SELECT * FROM subscriptions WHERE user_id=?"
    params = [session["user_id"]]

    if search:
        query += " AND (subscription_name LIKE ? OR category LIKE ?)"
        params.append(f"%{search}%")
        params.append(f"%{search}%")

    if sort_by == "name":
        query += " ORDER BY subscription_name ASC"
    elif sort_by == "price":
        query += " ORDER BY price ASC"
    elif sort_by == "renewal_date":
        query += " ORDER BY renewal_date ASC"

    cursor.execute(query, tuple(params))
    subscriptions = cursor.fetchall()

    total_monthly = 0
    subscriptions_with_status = []

    today = datetime.today().date()

    for sub in subscriptions:
        price = float(sub[4])
        billing_cycle = sub[5]

        if billing_cycle == "Monthly":
            total_monthly += price
        elif billing_cycle == "Yearly":
            total_monthly += price / 12

        renewal_date = datetime.strptime(sub[7], "%Y-%m-%d").date()
        days_left = (renewal_date - today).days

        if days_left < 0:
            status = "Expired"
        elif days_left <= 7:
            status = "Due Soon"
        else:
            status = "Active"

        subscriptions_with_status.append({
            "id": sub[0],
            "user_id": sub[1],
            "name": sub[2],
            "category": sub[3],
            "price": sub[4],
            "billing_cycle": sub[5],
            "start_date": sub[6],
            "renewal_date": sub[7],
            "status": status
        })

    conn.close()

    return render_template(
        "dashboard.html",
        subscriptions=subscriptions_with_status,
        total_monthly=total_monthly,
        search=search,
        sort_by=sort_by
    )

# Add Subscription
@app.route("/add_subscription", methods=["GET", "POST"])
def add_subscription():
    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":
        subscription_name = request.form["subscription_name"]
        category = request.form["category"]
        price = request.form["price"]
        billing_cycle = request.form["billing_cycle"]
        start_date = request.form["start_date"]
        renewal_date = request.form["renewal_date"]

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO subscriptions
            (user_id, subscription_name, category, price, billing_cycle, start_date, renewal_date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            session["user_id"],
            subscription_name,
            category,
            price,
            billing_cycle,
            start_date,
            renewal_date
        ))

        conn.commit()
        conn.close()

        return redirect("/dashboard")

    return render_template("add_subscription.html")

# Edit Subscription
@app.route("/edit_subscription/<int:id>", methods=["GET", "POST"])
def edit_subscription(id):
    if "user_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    if request.method == "POST":
        subscription_name = request.form["subscription_name"]
        category = request.form["category"]
        price = request.form["price"]
        billing_cycle = request.form["billing_cycle"]
        start_date = request.form["start_date"]
        renewal_date = request.form["renewal_date"]

        cursor.execute("""
            UPDATE subscriptions
            SET subscription_name=?, category=?, price=?, billing_cycle=?, start_date=?, renewal_date=?
            WHERE id=? AND user_id=?
        """, (
            subscription_name,
            category,
            price,
            billing_cycle,
            start_date,
            renewal_date,
            id,
            session["user_id"]
        ))

        conn.commit()
        conn.close()

        return redirect("/dashboard")

    cursor.execute(
        "SELECT * FROM subscriptions WHERE id=? AND user_id=?",
        (id, session["user_id"])
    )
    subscription = cursor.fetchone()
    conn.close()

    return render_template("edit_subscription.html", subscription=subscription)

# Delete Subscription
@app.route("/delete_subscription/<int:id>")
def delete_subscription(id):
    if "user_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM subscriptions WHERE id=? AND user_id=?",
        (id, session["user_id"])
    )

    conn.commit()
    conn.close()

    return redirect("/dashboard")

# Logout
@app.route("/logout")
def logout():
    session.pop("user_id", None)
    return redirect("/")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)