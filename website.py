from flask import Flask, render_template, request, redirect
import sqlite3

app = Flask(__name__)


# ---------------- DATABASE ----------------

def create_tables():

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    # Expenses table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            expense_name TEXT NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            payment_method TEXT NOT NULL,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        try:

            cursor.execute("""
                INSERT INTO users (name, email, password)
                VALUES (?, ?, ?)
            """, (name, email, password))

            conn.commit()
            conn.close()

            return "Registration successful! You can now login."

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
            SELECT * FROM users
            WHERE email = ? AND password = ?
        """, (email, password))

        user = cursor.fetchone()

        conn.close()

        if user:

            return redirect("/dashboard")

        else:

            return "Invalid email or password!"

    return render_template("login.html")


# ---------------- DASHBOARD ----------------

@app.route("/dashboard")
def dashboard():

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT expense_name, amount, category,
               payment_method, date
        FROM expenses
        ORDER BY id DESC
    """)

    expenses = cursor.fetchall()

    conn.close()

    return render_template(
        "dashboard.html",
        expenses=expenses
    )


# ---------------- ADD EXPENSE ----------------

@app.route("/add_expense", methods=["POST"])
def add_expense():

    expense_name = request.form["expense_name"]
    amount = request.form["amount"]
    category = request.form["category"]
    payment_method = request.form["payment_method"]

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO expenses
        (expense_name, amount, category, payment_method)
        VALUES (?, ?, ?, ?)
    """, (
        expense_name,
        amount,
        category,
        payment_method
    ))

    conn.commit()
    conn.close()

    return redirect("/dashboard")


# ---------------- START APPLICATION ----------------

create_tables()

if __name__ == "__main__":
    import os

    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=False
    )