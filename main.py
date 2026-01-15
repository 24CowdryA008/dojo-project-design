from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory, abort
import sqlite3, hashlib
import os
from create_db import create_database
from flask_login import LoginManager, login_required, current_user, login_user, logout_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config

# Do NOT run create_database() at import time in serverless environments.
# create_database()

# Ensure bookings table has choice columns (migration)
def ensure_bookings_schema():
    conn = sqlite3.connect("bookings.db")
    c = conn.cursor()
    c.execute("PRAGMA table_info(bookings)")
    existing = [row[1] for row in c.fetchall()]
    for col in ("choice1", "choice2", "choice3"):
        if col not in existing:
            try:
                c.execute(f"ALTER TABLE bookings ADD COLUMN {col} TEXT")
            except Exception:
                pass
    conn.commit()
    conn.close()

# Do NOT call ensure_bookings_schema() at import time; initialize via CLI or when running locally.
# ensure_bookings_schema()

# --------------------------------------------------
# Flask App Setup
# --------------------------------------------------
app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = app.config.get('SECRET_KEY') or 'dev-secret-key'
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
db_locale = 'users.db'

def get_db_connection():
    conn = sqlite3.connect("users.db")
    conn.row_factory = sqlite3.Row
    return conn

def get_user_bookings(user_id):
    conn = sqlite3.connect("bookings.db")
    c = conn.cursor()
    c.execute("SELECT id, choice1, choice2, choice3, date, time FROM bookings WHERE user_id = ?", (user_id,))
    bookings = c.fetchall()
    conn.close()
    return bookings


class User(UserMixin):
    def __init__(self, id, username, email, password_hash=None):
        self.id = str(id)
        self.username = username
        self.email = email
        self.password = password_hash


@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    user_row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    if user_row:
        return User(user_row["id"], user_row["username"], user_row["email"], user_row["password"])
    return None

# ------------------------------------------------
# App Routes
# ------------------------------------------------

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/courses')
def courses():
    return render_template('courses.html')

@app.route('/bookings', methods=['GET', 'POST'])
@login_required
def bookings():
    if request.method == 'POST':
        choice1 = request.form.get('choice1')
        choice2 = request.form.get('choice2')
        choice3 = request.form.get('choice3')
        date = request.form.get('date')
        time = request.form.get('time')

        # Keep legacy 'course' column populated (use first choice)
        course = choice1 if choice1 else ''

        conn = sqlite3.connect("bookings.db")
        c = conn.cursor()
        c.execute("INSERT INTO bookings (user_id, course, choice1, choice2, choice3, date, time) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (current_user.id, course, choice1, choice2, choice3, date, time))
        conn.commit()
        conn.close()

        flash("Your booking has been submitted!", "success")
        return redirect(url_for('bookings'))

    # Fetch bookings including choices and time
    conn = sqlite3.connect("bookings.db")
    c = conn.cursor()
    c.execute("SELECT id, choice1, choice2, choice3, date, time FROM bookings WHERE user_id = ?", (current_user.id,))
    user_bookings = c.fetchall()
    conn.close()

    return render_template('bookings.html', user_bookings=user_bookings)

@app.route("/cancel_booking/<int:booking_id>")
@login_required
def cancel_booking(booking_id):
    conn = sqlite3.connect(app.config["BOOKINGS_DB"])
    c = conn.cursor()

    # Only delete if booking belongs to this user
    c.execute("DELETE FROM bookings WHERE id = ? AND user_id = ?", 
            (booking_id, current_user.id))

    conn.commit()
    conn.close()

    flash("Booking cancelled.", "info")
    return redirect(url_for("bookings"))

#This code is so that users can login and register (logging in is required)
@app.route("/Login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username_or_email = request.form["uname"]
        password = request.form["psw"]

        conn = get_db_connection()
        user = conn.execute(
            "SELECT * FROM users WHERE username = ? OR email = ?",
            (username_or_email, username_or_email),
        ).fetchone()
        conn.close()

        if user and check_password_hash(user["password"], password):
            # Create a Flask-Login user and log them in
            user_obj = User(user["id"], user["username"], user["email"], user["password"])
            login_user(user_obj)

            flash("Login successful!", "success")
            return redirect(url_for("home"))
        else:
            flash("Invalid username/email or password.", "danger")
            return redirect(url_for("login"))

    
    return render_template("login.html")

@app.route("/Register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        forename = request.form["forename"]
        surname = request.form["surname"]
        email = request.form["email"]
        username = request.form["uname"]
        password = request.form["psw"]

        # Hash password before storing (for security)
        hashed_password = generate_password_hash(password)

        try:
            conn = get_db_connection()
            conn.execute(
                "INSERT INTO users (forename, surname, email, username, password) VALUES (?, ?, ?, ?, ?)",
                (forename, surname, email, username, hashed_password),
            )
            conn.commit()
            conn.close()

            flash("Account created successfully! You can now log in.", "success")
            return redirect(url_for("login")) 

        except sqlite3.IntegrityError:
            flash("Username or email already exists. Please try again.", "danger")
            return redirect(url_for("register"))

    return render_template("register.html")

@app.route("/logout")
def logout():
    # Clear Flask session and logout via Flask-Login
    session.clear()
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))

@app.route('/termsandconditions')
def termsandconditions():
    return render_template('termsandconditions.html')

# Serve favicons directly so requests to /favicon.ico and /favicon.png succeed on Vercel
@app.route('/favicon.ico')
def favicon():
    static_dir = os.path.join(app.root_path, 'static')
    ico_path = os.path.join(static_dir, 'favicon.ico')
    png_path = os.path.join(static_dir, 'favicon.png')

    if os.path.exists(ico_path):
        return send_from_directory(static_dir, 'favicon.ico', mimetype='image/vnd.microsoft.icon')
    if os.path.exists(png_path):
        return send_from_directory(static_dir, 'favicon.png', mimetype='image/png')

    # Neither favicon exists; return 404 so caller knows it's not available
    abort(404)

@app.route('/favicon.png')
def favicon_png():
    static_dir = os.path.join(app.root_path, 'static')
    png_path = os.path.join(static_dir, 'favicon.png')
    if os.path.exists(png_path):
        return send_from_directory(static_dir, 'favicon.png', mimetype='image/png')
    ico_path = os.path.join(static_dir, 'favicon.ico')
    if os.path.exists(ico_path):
        return send_from_directory(static_dir, 'favicon.ico', mimetype='image/vnd.microsoft.icon')
    abort(404)

from flask.cli import with_appcontext
import click

@app.cli.command('init-db')
@with_appcontext
def init_db_command():
    """Initialize application databases (users + bookings)."""
    create_database()
    ensure_bookings_schema()
    click.echo('Databases initialized.')

if __name__ == '__main__':
    # When running the dev server locally, initialize DBs if missing.
    try:
        create_database()
        ensure_bookings_schema()
    except Exception:
        # Don't crash the dev server if DB init fails unexpectedly
        pass
    
    app.run(debug=True) # When updating the site, just refresh the page rather than having to restart the whole program.


