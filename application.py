import os

from flask import Flask, session, render_template, request, redirect, url_for, session
from flask_bcrypt import Bcrypt
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from datetime import datetime


app = Flask(__name__)
bcrypt = Bcrypt(app)

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


@app.route("/")
def index():
    return render_template("login.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        try:
            username = request.form["username"]
            password = request.form["password"]
            if username == "" or password == "":
                error = "Please enter your username and password"
                return render_template("loginForm.html", error=error)
        except:
            error = "Please enter your username and password"
            return render_template("loginForm.html", error=error)
        # Check if there exists a user with that username:
        user = db.execute(
            "SELECT * FROM users WHERE (username = :username)", {"username": username}
        ).fetchone()
        if user:
            # If password is correct log the user in and redirect to the home page
            if bcrypt.check_password_hash(user[2], password):
                session["first-name"] = user[4]
                session["user_id"] = user[0]
                session["isAuthenticated"] = True
                return redirect(url_for("home"))
            # If the password is incorrect render the log in form with appropriate error.
            error = "Your password is incorrect"
            return render_template("loginForm.html", error=error)
        error = "There is no account with that username, check for a mistype or register instead!"
        return render_template("loginForm.html", error=error)
    return render_template("loginForm.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        try:
            error = "You need to fill out all the fields!"
            username = request.form["username"]
            first_name = request.form["fname"]
            last_name = request.form["lname"]
            email = request.form["email"]
            terms = request.form["terms"]
            if request.form["pass1"] == request.form["pass2"]:
                password = bcrypt.generate_password_hash(request.form["pass1"]).decode(
                    "utf-8"
                )
        except:
            return render_template("registerForm.html", error=error)
        if not password:
            error = "Your passwords do not match!"
            return render_template("registerForm.html", error=error)
        error = "This is embarrasing...our server is down please try again soon someone is fixing it!!"

        # Check if the username exists
        if db.execute(
            "SELECT * FROM users WHERE (username = :username)", {"username": username}
        ).fetchone():
            error = "There is already a user with this username!"
            return render_template("registerForm.html", error=error)
        # If user exists and all fields valid insert user to database
        db.execute(
            "INSERT INTO users (username, passwordHash, email, first_name, last_name) VALUES (:username, :password, :email, :fname, :lname)",
            {
                "username": username,
                "password": password,
                "email": email,
                "fname": first_name,
                "lname": last_name,
            },
        )

        db.commit()

        # If successful log the user in and redirect to the home page.
        session["isAuthenticated"] = True
        session["first-name"] = first_name
        session["user_id"] = user[0]
        return redirect(url_for("home"))
    return render_template("registerForm.html")


@app.route("/home", methods=["GET", "POST"])
def home():
    if request.method == "POST" and session.get("isAuthenticated"):
        query = request.form["query"].lower()
        books = db.execute(
            'SELECT * FROM "books" WHERE LOWER(books.title) LIKE :query OR LOWER(books.author) LIKE :query OR books.isbn = :query',
            {"query": "%" + query + "%"},
        ).fetchall()
        return render_template("home.html", books=books, user=session.get("first-name"))
    if session.get("isAuthenticated"):
        books = db.execute('SELECT * FROM "books" LIMIT 25').fetchall()
        return render_template("home.html", books=books, user=session.get("first-name"))
    return redirect(url_for("login"))


@app.route("/book/<string:isbn>", methods=['GET', 'POST'])
def book(isbn):
    if session.get("isAuthenticated") and request.method == "POST":
        #Check there exists a book with the given isbn
        book = db.execute(
            "SELECT * FROM books WHERE(books.isbn) = :isbn", {"isbn": isbn}
        ).fetchone()

        if not book:
            error = "Unfortunately there is no book with that isbn, go back to our search page!"
            return redirect(url_for('home'))

        #Get all reviews on that book

        reviews = db.execute(
            "SELECT * FROM reviews JOIN users ON (users.user_id = reviews.user_id) WHERE(reviews.book_id) = :book_id ORDER BY reviews.review_timestamp DESC", {"book_id": book[0]}
        ).fetchall()

        if not reviews:
            reviews = []

        #Check if the user has already written a review
        user_review = db.execute(
            "SELECT * FROM reviews WHERE (user_id = :user_id AND book_id = :book_id)" , 
            {"user_id": session.get("user_id"), "book_id": book[0]}
        ).fetchone()

        try:
            rating = request.form["rating"]
            comment = request.form["comment"]
        except:
            review_error = "You must include both a rating and a comment in your review!"
            return render_template("book.html", book=book, review_error=review_error, user_review=user_review, reviews=reviews)

        if not user_review:
            #If the user has no review then give option to create a new review 
            
            db.execute(
                "INSERT INTO reviews (user_id, book_id, rating, review_comment, review_timestamp) VALUES (:user_id, :book_id, :rating, :review_comment, :review_timestamp)",
                {"user_id": session.get("user_id"), "book_id": book[0], "rating": rating, "review_comment": comment, "review_timestamp": datetime.now()}
            )

            db.commit()

        if user_review:
            #If the user already has a review this logic will allow them to update their review
            db.execute(
                "UPDATE reviews SET rating = :rating, review_comment = :review_comment, review_timestamp = :review_timestamp WHERE review_id = :review_id",
                {"rating": rating, "review_comment": comment, "review_timestamp": datetime.now(), "review_id": user_review[0]}
            )

            db.commit()

        #Get updated reviews

        reviews = db.execute(
            "SELECT * FROM reviews JOIN users ON (users.user_id = reviews.user_id) WHERE(reviews.book_id) = :book_id ORDER BY reviews.review_timestamp DESC", {"book_id": book[0]}
        ).fetchall()

        if not reviews:
            reviews = []

        return render_template("book.html", book=book, reviews=reviews, user_review=user_review)

    if session.get("isAuthenticated"):
        #Get data on the book
        book = db.execute(
            "SELECT * FROM books WHERE(books.isbn) = :isbn", {"isbn": isbn}
        ).fetchone()

        if not book:
            error = "Unfortunately there is no book with that isbn, go back to our search page!"
            return redirect(url_for('home'))
        #Check if the user has already written a review
        user_review = db.execute(
            "SELECT * FROM reviews WHERE (user_id = :user_id AND book_id = :book_id)" , 
            {"user_id": session.get("user_id"), "book_id": book[0]}
        ).fetchone()

        #Get all reviews on that book
        try:
            reviews = db.execute(
                "SELECT * FROM reviews JOIN users ON (users.user_id = reviews.user_id) WHERE(reviews.book_id) = :book_id ORDER BY reviews.review_timestamp DESC", {"book_id": book[0]}
            ).fetchall()
        except:
            reviews = []
        #Get review of current user on that book
        return render_template("book.html", book=book, reviews=reviews, user_review=user_review)
    return redirect(url_for("login"))


@app.route("/logout")
def logout():
    session["isAuthenticated"] = False
    session["first-name"] = None
    session["user_id"] = None
    return redirect(url_for("index"))
