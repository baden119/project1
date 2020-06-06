import os
import requests

from flask import Flask, session, redirect, render_template, request
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

#  Some Helper Functions

def match_check(password, confirmation):
    """Checks password and confirmation inputs are matching"""

    if len(password) != len(confirmation): return False

    for i in range(len(password)):
        if password[i] != confirmation[i]: return False

    return True


@app.route("/")
def index():

    # Login Required, redirect to /login if no session.
    if session.get("user_id") is None:
            return redirect("/login")

    # Get user info from users table in database
    user_info = db.execute("SELECT * FROM users WHERE id = :user_id",
                            {"user_id":session["user_id"]}).fetchone()

    return render_template("index.html", username=user_info.username)

@app.route("/book/<isbn>")
def book(isbn):
    """Lists details about a single book."""

    user_info = db.execute("SELECT * FROM users WHERE id = :user_id",
                            {"user_id":session["user_id"]}).fetchone()

    db_query = db.execute("SELECT * FROM books WHERE isbn = :isbn",
                        {"isbn": isbn}).fetchone()

    return render_template("book.html", db_query=db_query, username=user_info.username)

@app.route("/error")
def error():

    return render_template("error.html", error="Error Button Pushed.")

@app.route("/login", methods=["GET", "POST"])
def login():

    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

        # Query database for username
        user_data = db.execute("SELECT * FROM users WHERE username = :username",
                          {"username":username}).fetchone()

        # Ensure username exists and password is correct
        if user_data is None:
            return render_template("error.html", error="Invalid Username")

        # Check that passwords match
        if not (match_check(password, user_data.password)):
            return render_template("error.html", error="Wrong Password")

        # Remember which user has logged in
        session["user_id"] = user_data.id

        # Redirect user to home page
        return redirect("/")

    else:
        return render_template("login.html")

@app.route("/search", methods=["GET", "POST"])
def search():

    user_info = db.execute("SELECT * FROM users WHERE id = :user_id",
                            {"user_id":session["user_id"]}).fetchone()

    query=request.form.get("query_data")
    query = '%' + query + '%'
    criteria=request.form.get("criteria")

    ###WHY DOSENT THIS WORK????###
    # db_query = db.execute("SELECT * FROM books WHERE :criteria LIKE :query",
    #                         {"criteria": criteria, "query": query}).fetchall()


    ##CONDITIONAL STATEMENTS###

    if criteria == 'title':
        print("conditional title detected")

        db_query = db.execute("SELECT * FROM books WHERE title LIKE :query",
                            {"query": query}).fetchall()

    elif criteria == 'author':
        print("conditional author detected")

        db_query = db.execute("SELECT * FROM books WHERE author LIKE :query",
                            {"query": query}).fetchall()

    else:
        print("conditional isbn detected")

        db_query = db.execute("SELECT * FROM books WHERE isbn LIKE :query",
                            {"query": query}).fetchall()


    return render_template("results.html", db_query=db_query, username=user_info.username)


@app.route("/register", methods=["GET", "POST"])
def register():

    """Register user"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        username=request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # Check that passwords match
        if not (match_check(password, confirmation)):
            return render_template("error.html", error="Passwords didn't match.")

        # Check username availability in database
        unavailable = db.execute("SELECT * FROM users WHERE username = :username",
                        {"username":username}).fetchone()

        if unavailable:
            return render_template("error.html", error="Username Already Exists")

        # Insert new user into database, storing plaintext
        db.execute("INSERT INTO users (username, password) VALUES(:username, :password)",
                {"username":username, "password":password})

        db.commit()

        # Log user in
        user_data = db.execute("SELECT * FROM users WHERE username = :username",
                          {"username":username}).fetchone()

        session["user_id"] = user_data.id

        # Redirect user to home page
        return redirect("/")

    else:
        return render_template("register.html")
