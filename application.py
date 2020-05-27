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

    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():

    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        username=request.form.get("username")
        password = request.form.get("password")

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          {"username":username}).fetchone()
        if rows is None:
            return render_template("error.html", error="Invalid Username")

        print(type(rows))
        print()
        print(rows)


        print(f"{rows.id}")
        print(f"{rows.password}")

        # # Ensure username exists and password is correct
        # if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
        #     return apology("invalid username and/or password", 400)

        # Remember which user has logged in
        session["user_id"] = rows.id


        # Get user info from users table in database
        user_info = db.execute("SELECT * FROM users WHERE id = :user_id",
                                {"user_id":session["user_id"]}).fetchone()
        print("user info:")
        print(f"{user_info.id}")
        print(f"{user_info.username}")
        print(f"{user_info.password}")

        # Redirect user to home page
        return redirect("/")

    else:
        return render_template("login.html")

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
                        {"username":username})
        if unavailable:
            return render_template("error.html", error="Username Already Exists")

        # Insert new user into database, storing plaintext
        result = db.execute("INSERT INTO users (username, password) VALUES(:username, :password)",
                    {"username":username, "password":password})

        db.commit()

        # # Log user in
        # rows = db.execute("SELECT * FROM users WHERE username = :username",
        #                   username=request.form.get("username"))
        #
        # session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    else:
        return render_template("register.html")

@app.route("/error")
def error():

    return render_template("error.html", error="Error Button Pushed.")
