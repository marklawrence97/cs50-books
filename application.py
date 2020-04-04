import os

from flask import Flask, session, render_template, request, redirect, url_for, session
from flask_bcrypt import Bcrypt
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker


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
    return render_template('login.html')

@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            username = request.form['username']
            password = request.form['password']
            if username == "" or password == "":
                error = "Please enter your username and password"
                return render_template('loginForm.html', error=error)
        except:
            error = "Please enter your username and password"
            return render_template('loginForm.html', error=error)
        passwordHash = db.execute("SELECT passwordHash FROM users WHERE (username = :username)", {"username": username}).fetchone()[0]
        
        #If password is correct log the user in and redirect to the home page
        if bcrypt.check_password_hash(passwordHash, password):
            session["isAuthenticated"] = True
            return redirect(url_for('home'))

        #If the password is incorrect render the log in form with appropriate error.
        error = "Your password is incorrect"
        return render_template('loginForm.html', error=error)

    return render_template('loginForm.html')

@app.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try: 
            error = "You need to fill out all the fields!"
            username = request.form['username']
            first_name = request.form['fname']
            last_name = request.form['lname']
            email = request.form['email']
            terms = request.form['terms']
            if request.form['pass1'] == request.form['pass2']:
                password = bcrypt.generate_password_hash(request.form['pass1']).decode('utf-8')
        except:
            return render_template('registerForm.html', error=error)
        if not password:
            error = "Your passwords do not match!"
            return render_template('registerForm.html', error=error)

        error = "This is embarrasing...our server is down please try again soon someone is fixing it!!"
        
        #Check if the username exists
        if (db.execute("SELECT * FROM users WHERE (username = :username)", {"username": username}).fetchone()):
            error = "There is already a user with this username!"
            return render_template('registerForm.html', error=error)            
        
        #If user exists and all fields valid insert user to database
        db.execute("INSERT INTO users (username, passwordHash, email, first_name, last_name) VALUES (:username, :password, :email, :fname, :lname)", {
            "username": username, "password": password, "email": email, "fname": first_name, "lname": last_name
        })

        db.commit()

        #If successful log the user in and redirect to the home page.
        session["isAuthenticated"] = True
        return redirect(url_for('home'))
    return render_template('registerForm.html')

@app.route("/home")
def home():
    if session.get("isAuthenticated"):
        books = db.execute('SELECT * FROM "books" LIMIT 25').fetchall()
        return render_template('home.html', books=books)
    return redirect(url_for('login'))

@app.route("/book")
def book():
    if session.get("isAuthenticated"):
        return render_template('book.html')
    return redirect(url_for('login'))