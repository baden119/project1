import os
import requests
import time

from flask import Flask, jsonify, session, redirect, render_template, request, url_for
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

    book_info = db.execute("SELECT * FROM books WHERE isbn = :isbn",
                        {"isbn": isbn}).fetchone()

    reviews = db.execute("SELECT review_text, rating, submission_dt, username FROM reviews JOIN users ON reviews.reviewer_id = users.id WHERE isbn = :isbn ORDER BY submission_dt DESC;",
                        {"isbn": isbn}).fetchall()


    # Getting info object from goodreads API
    res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "biFJnnfgoPuXUMSwYm1rw", "isbns": isbn})

    # Accessing average goodreads rating and review count from API data
    api_info = res.json()
    book_info_dict = api_info["books"][0]
    goodreads_reviewcount = str(book_info_dict["reviews_count"])
    goodreads_average = book_info_dict["average_rating"]

    if len(reviews) == 0:
        return render_template("book.html", book_info=book_info, goodreads_average = goodreads_average, goodreads_reviewcount = goodreads_reviewcount, local_average="No Ratings Yet", username=user_info.username, message = "No User Reviews, Would you like to write one?")
    # Calculating average rating from local users reviews
    ratings=[]
    for review in reviews:
        ratings.append(review.rating)
    local_average = (round((sum(ratings) / len(ratings)), 2))

    return render_template("book.html", book_info=book_info, local_average=local_average, goodreads_average = goodreads_average, goodreads_reviewcount = goodreads_reviewcount, reviews=reviews, username=user_info.username)

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
        db.execute("INSERT INTO users (username, password, created) VALUES(:username, :password, :created)",
                {"username":username, "password":password, "created":time.strftime('%Y-%m-%d %H:%M:%S')})

        db.commit()

        # Log user in
        user_data = db.execute("SELECT * FROM users WHERE username = :username",
                          {"username":username}).fetchone()

        session["user_id"] = user_data.id

        # Redirect user to home page
        return redirect("/")

    else:
        return render_template("register.html")

@app.route("/review/<isbn>", methods=["GET", "POST"])
def review(isbn):
    """Write a book review"""
    # Login Required, redirect to /login if no session.
    if session.get("user_id") is None:
        return redirect("/login")

    user_info = db.execute("SELECT * FROM users WHERE id = :user_id",
    {"user_id":session["user_id"]}).fetchone()

    db_query = db.execute("SELECT * FROM books WHERE isbn = :isbn",
    {"isbn": isbn}).fetchone()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":


        # Request review data from html and return error if it's missing.
        rating = request.form.get("rating")
        review_text = request.form.get("review_text")
        if (rating is None) or len(review_text) == 0:
            return render_template("error.html", error="Review must include text and a rating out of 5.")

        # Insert review into reviews table in database
        db.execute("INSERT INTO reviews (reviewer_id, isbn, rating, review_text, submission_dt) VALUES (:reviewer_id, :isbn, :rating, :review_text, :submission_dt)",
        {"reviewer_id":session["user_id"], "isbn":isbn, "rating":rating, "review_text":review_text, "submission_dt":time.strftime('%Y-%m-%d %H:%M:%S')})
        db.commit()

        return redirect(url_for('book', isbn=isbn))

    else:
        return render_template("review.html", db_query=db_query, username=user_info.username)

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
        db_query = db.execute("SELECT * FROM books WHERE title LIKE :query",
        {"query": query}).fetchall()

    elif criteria == 'author':
        db_query = db.execute("SELECT * FROM books WHERE author LIKE :query",
        {"query": query}).fetchall()

    else:
        db_query = db.execute("SELECT * FROM books WHERE isbn LIKE :query",
        {"query": query}).fetchall()

    if len(db_query) == 0:
        return render_template("error.html", error="No matching results in database.")


    return render_template("results.html", db_query=db_query, username=user_info.username)

@app.route("/api/book/<isbn>")
def api_book(isbn):

    # Get info from data tables
    book_info = db.execute("SELECT * FROM books WHERE isbn = :isbn",
                        {"isbn": isbn}).fetchone()

    raw_ratings = db.execute("SELECT rating FROM reviews WHERE isbn = :isbn",
                        {"isbn": isbn}).fetchall()

    # Return error if book not found in database
    if book_info is None:
        return jsonify({"error": "Invalid ISBN :("}), 404

    # Access rating values in raw data and calculate an average score
    ratings = []
    for rating in raw_ratings:
        ratings.append(rating.values()[0])
    ratings_average = (round((sum(ratings) / len(ratings)), 2))

    # Collate data and return in JSON format
    return jsonify({
    "isbn": book_info.isbn,
    "title": book_info.title,
    "author": book_info.author,
    "year": book_info.year,
    "review_count": len(ratings),
    "average_score": ratings_average
    })
