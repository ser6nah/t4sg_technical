"""Generates website for WHO to keep track of what vaccines are getting distributed where"""

### Import libraries
import sqlite3
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
from random import sample
from collections import Counter
from helpers import apology, login_required 


# Make a connection to blog.db database
conn = sqlite3.connect('./vaccinations.db', check_same_thread=False, isolation_level=None)
db = conn.cursor()


# Configure application
app = Flask(__name__)


# Ensure templates are auto-reloaded
# From CS50 Finance starter code
app.config["TEMPLATES_AUTO_RELOAD"] = True


# Ensure responses aren't cached
# From CS50 Finance starter code
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Configure session to use filesystem (instead of signed cookies)
# From CS50 Finance Starter Code
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


### Page for homepage
@app.route("/", methods=["GET"])
def index():
    """Render homepage"""
    # If user isn't logged in
    if not session.get("user_id"):
        return render_template("homepage.html")

    # If user is logged in
    else:
        # Get logged in user's email
        email = db.execute("SELECT email FROM users WHERE id = ?", (session.get("user_id"),)).fetchone()[0]
        # Get public history in order of recency
        recent_reports = db.execute("SELECT vaccine, quantity, location, date FROM posts WHERE id = ? ORDER BY timestamp DESC LIMIT 100", 
                            (session.get("user_id"))).fetchall()

        # Render homepage
        return render_template("data_homepage.html", email=email, reports=recent_reports)
    

### Page for reporting # of vaccines delivered where and when
@app.route("/report", methods=["GET", "POST"])
@login_required
def report():
    """Create new post"""
    if request.method == "POST":
        # Prepare for database insertion
        if request.form.get("notes"):
            notes = request.form.get("notes")
        else: 
            notes = None

        # Add vaccine update to database
        db.execute("INSERT INTO posts (user_id, vaccine, quantity, location, date, notes) VALUES(?, ?, ?, ?, ?)", 
                  (session.get("user_id"), request.form.get("vaccine"), request.form.get("quantity"), 
                  request.form.get("location"), request.form.get("date"), notes)) 

        # Redirect to page with their history of vaccination updates
        return redirect("/history")
        
    # User reached route via GET (as by clicking a link or via redirect)
    else:
        """Get post template"""
        return render_template("report.html")


### Page for users' history of vaccination distribution reports
@app.route("/history", methods=["GET", "POST"])
@login_required
def history():
    """View previous reports made by user"""
    # Get history in order of recency
    reports = db.execute("SELECT vaccine, quantity, location, date, notes, timestamp FROM posts WHERE id = ? ORDER BY timestamp DESC", (session.get("user_id"))).fetchall()

    if reports is None:
        return apology("You haven't made any reports yet!")
        
    # # Get reports as a list of lists
    # reports_list = [[x[2], x[3], x[4], x[5], x[6]] for x in reports]
    # for report_list in reports_list:
    #     trending_post[2] = db.execute("SELECT username FROM users WHERE id = ?", (trending_post[2],)).fetchall()[0]

    # Render history page
    return render_template("history.html", reports=reports)


### Page for registering 
@app.route("/register", methods=["GET", "POST"])
def register():
    session.clear()

    """Register user"""
    if request.method == "POST":

        # If email hasn't yet been registered
        if db.execute("SELECT * FROM users WHERE email = ?", (request.form.get("email"),)).fetchone() is not None:
            return apology("This email has already been used to create an account.")

        # Ensure passwords match
        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("Passwords do not match")

        # Insert account into database
        email = request.form.get("email").lower()
        hash_code = generate_password_hash(request.form.get("password"), method='pbkdf2:sha256', salt_length=8)
        db.execute("INSERT INTO users (email, hash) VALUES(?, ?)", (email, hash_code))

        # Log user in
        session["user_id"] = db.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()[0]
        
        # Return to homepage
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        # Render registration page
        return render_template("register.html")


### Page for logging in
# Some lines from CS50 Finance starter code
@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure email was submitted
        if not request.form.get("email"):
            return apology("must provide email", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for email
        row = db.execute("SELECT * FROM users WHERE email=?", (request.form.get("email"),)).fetchone()

        # Ensure email exists and password is correct
        if not row or not check_password_hash(row[2], request.form.get("password")):
            return apology("invalid email and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = row[0]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


# Page for logging out
# From CS50 Finance starter code
@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


### Page for changing user password
@app.route("/password", methods=["GET", "POST"])
@login_required
def changepassword():
    """Let user change their password"""

    if request.method == "POST":
        # Ensure user inputed an "old password"
        if not request.form.get("old password"):
            return apology("must provide old password")

        # Ensure user inputed a "new password"
        elif not request.form.get("new password"):
            return apology("must provide new password")

        # Ensure user inputed a confirmation
        elif not request.form.get("confirmation"):
            return apology("must provide confirmation")

        # Ensure old password is correct
        real_hash = db.execute("SELECT hash FROM users WHERE id = ?", (session["user_id"],)).fetchone()[0] 
        if not check_password_hash(real_hash, request.form.get("old password")):
            return apology("old password is incorrect")

        # Ensure new password and confirmation match
        elif request.form.get("new password") != request.form.get("confirmation"):
            return apology("the new passwords do not match")

        # Change password
        hash_code = generate_password_hash(request.form.get("new password"), method='pbkdf2:sha256', salt_length=8)
        db.execute("UPDATE users SET hash = ? WHERE id = ?", (hash_code, session["user_id"]))

        # Redirect user to log out
        return redirect("/logout")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("password.html")


def errorhandler(e):
    """Handle error"""
    # From CS50 Finance starter code
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
# From CS50 Finance starter code
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
