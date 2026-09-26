from flask import Flask, render_template, request, redirect, session
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

app.secret_key = "student-expense-tracker-secret-key"


# ---------------- DATABASE ----------------

def create_tables():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            budget REAL DEFAULT 0
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            expense_name TEXT NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            payment_method TEXT NOT NULL,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    conn.commit()
    conn.close()


# ---------------- HOME ----------------

@app.route("/")
def home():
    return render_template("index.html")


# ---------------- REGISTER ----------------

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        # Hash password before storing it
        hashed_password = generate_password_hash(password)

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        try:

            cursor.execute("""
                INSERT INTO users
                (name, email, password, budget)
                VALUES (?, ?, ?, ?)
            """, (
                name,
                email,
                hashed_password,
                0
            ))

            conn.commit()
            conn.close()

            return redirect("/login")

        except sqlite3.IntegrityError:

            conn.close()

            return "This email is already registered. Please login."

    return render_template("register.html")


# ---------------- LOGIN ----------------

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, name, password
            FROM users
            WHERE email = ?
        """, (email,))

        user = cursor.fetchone()

        conn.close()

        if user:

            user_id = user[0]
            user_name = user[1]
            stored_password = user[2]

            # Check hashed password
            if check_password_hash(stored_password, password):

                session["user_id"] = user_id
                session["user_name"] = user_name

                return redirect("/dashboard")

        return "Invalid email or password!"

    return render_template("login.html")


# ---------------- LOGOUT ----------------

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/login")


# ---------------- DASHBOARD ----------------

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # Get only this user's expenses
    cursor.execute("""
        SELECT expense_name,
               amount,
               category,
               payment_method,
               date
        FROM expenses
        WHERE user_id = ?
        ORDER BY id DESC
    """, (user_id,))

    expenses = cursor.fetchall()

    # Get this user's budget
    cursor.execute("""
        SELECT budget
        FROM users
        WHERE id = ?
    """, (user_id,))

    result = cursor.fetchone()

    budget = result[0] if result else 0

    conn.close()

    return render_template(
        "dashboard.html",
        expenses=expenses,
        budget=budget,
        user_name=session["user_name"]
    )


# ---------------- ADD EXPENSE ----------------

@app.route("/add_expense", methods=["POST"])
def add_expense():

    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    expense_name = request.form["expense_name"]
    amount = request.form["amount"]
    category = request.form["category"]
    payment_method = request.form["payment_method"]

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO expenses
        (user_id, expense_name, amount, category, payment_method)
        VALUES (?, ?, ?, ?, ?)
    """, (
        user_id,
        expense_name,
        amount,
        category,
        payment_method
    ))

    conn.commit()
    conn.close()

    return redirect("/dashboard")


# ---------------- SET BUDGET ----------------

@app.route("/set_budget", methods=["POST"])
def set_budget():

    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    budget = request.form["budget"]

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE users
        SET budget = ?
        WHERE id = ?
    """, (budget, user_id))

    conn.commit()
    conn.close()

    return redirect("/dashboard")


# ---------------- CREATE DATABASE ----------------

create_tables()


# ---------------- RUN APP ----------------

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=False
    )