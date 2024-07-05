from flask import Flask, render_template, redirect, flash, session, url_for, request
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin, current_user
from sqlalchemy import create_engine, Column, Integer, String, Date
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from werkzeug.security import generate_password_hash, check_password_hash
from forms import RegistrationForm, LoginForm, AuthorForm, GenreForm, PublisherForm, BookForm, OrderForm, ReviewForm, EditBookForm, StarRatingForm
from models import add_author_to_db, add_genre_to_db, add_publisher_to_db, add_book_to_db, add_review_to_db, update_book_in_db
import os
from werkzeug.utils import secure_filename
import mysql.connector as MySQL
from mysql.connector import Error
from datetime import date
import mysql.connector
from flask_wtf.csrf import CSRFProtect
from textblob import TextBlob
import logging
import random, string
from flask import abort
from werkzeug.exceptions import Unauthorized


# INITIALISE FLASK APPLICATION
app = Flask(__name__)
app.secret_key = 'your_secret_key'


# TO STORE BOOK STORES 
UPLOAD_FOLDER = 'static/images'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


# ENSURE THAT UPLOADED FOLDER EXISTS IF NOT CREATE ONE
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


# Configure SQLAlchemy
# DATABASE CONNECTION THROUGH SQLALCHEMY
engine = create_engine("mysql+pymysql://root:mysqlpassword@localhost:3306/bookhaven")
Session = scoped_session(sessionmaker(bind=engine))
Base = declarative_base()
Base.metadata.create_all(engine)


# MYSQL DATABASE CONNECTION 
def create_db_connection():
    try:
        # Establish a connection to the database
        conn = MySQL.connect(
            host="localhost",
            user="root",
            password="mysqlpassword",
            database="bookhaven"
        )
        return conn

    except Error as e:
        print("Error connecting to MySQL database:", e)
        return None


# FLASK-LOGIN SETUP
login_manager = LoginManager()
login_manager.init_app(app)


# ADMIN CREDENTIALS
ADMIN_EMAIL = 'admin@gmail.com'
ADMIN_PASSWORD_HASH = generate_password_hash('adminpassword')  # Example, should be hashed


#THE LIST OF ALLOWED FILES 
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


#TO GROUP THE REVIEWS
def analyze_sentiment(text):
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity
    if polarity > 0.5:
        return 'positive'
    elif polarity < 0:
        return 'negative'
    else:
        return 'neutral'


# USER CLASS
class User(UserMixin, Base):
    __tablename__ = 'users'
    
    user_id = Column(Integer, primary_key=True, autoincrement=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    age = Column(Integer)
    contact = Column(String(20))
    username = Column(String(50), unique=True, nullable=False)
    address = Column(String(255))
    password = Column(String(255), nullable=False)  # Store the hashed password
    
    def __init__(self, first_name, last_name, email, age, contact, username, address, password):
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.age = age
        self.contact = contact
        self.username = username
        self.address = address
        self.set_password(password)  # Hash the password during initialization

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def get_id(self):
        return str(self.user_id)

    @classmethod
    def query(cls):
        return Session.query(cls)


# AUTHOR CLASS
class Author(Base):
    __tablename__ = 'authors'
    
    author_id = Column(Integer, primary_key=True, autoincrement=True)
    author_name = Column(String(255), nullable=False)
    biography = Column(String(1000))
    birth_date = Column(Date)
    nationality = Column(String(100))

    def __init__(self, author_name, biography, birth_date, nationality):
        self.author_name = author_name
        self.biography = biography
        self.birth_date = birth_date
        self.nationality = nationality


# USER LOADER FUNCTION FOR FLASK LOGIN
# TO GET THE USER ID 
@login_manager.user_loader
def load_user(user_id):
    return User.query().get(int(user_id))


# ADMIN ROUTE
@app.route('/admin', methods=['GET'])
@login_required  # Ensures only authenticated users can access
def admin():
    # Check if the current user is the admin
    if current_user.email != ADMIN_EMAIL:
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('home'))  # Redirect to home or login page

    # Render the admin template
    return render_template('admin.html', title='Admin Panel')


# SIGN UP(NEW USER)
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        if User.query().filter_by(email=form.email.data).first():
            flash('Email already exists. Please use a different email.', 'danger')
        else:
            new_user = User(
                first_name=form.first_name.data,
                last_name=form.last_name.data,
                email=form.email.data,
                age=form.age.data,
                contact=form.contact.data,
                username=form.username.data,
                address=form.address.data,
                password=form.password.data
            )
            Session.add(new_user)
            Session.commit()
            flash('Registration successful. You can now log in.', 'success')
            return redirect(url_for('login'))
    return render_template('register.html', form=form, title='Register')


# HOME PAGE
@app.route('/')
def home():
    conn = create_db_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        
        # Query to fetch book data with average rating and cover image path
        query = """
            SELECT b.book_id, b.title, a.author_name, g.genre_name, p.publisher_name, b.price,
                   AVG(s.stars) AS avg_rating, b.cover_image
            FROM books b
            INNER JOIN authors a ON b.author_id = a.author_id
            INNER JOIN genre g ON b.genre_id = g.genre_id
            INNER JOIN publishers p ON b.publisher_id = p.publisher_id
            LEFT JOIN stars s ON b.book_id = s.book_id
            GROUP BY b.book_id
        """
        
        cursor.execute(query)
        books_data = cursor.fetchall()
        
        conn.close()
        
        return render_template('home.html', books=books_data)
    else:
        return "Failed to connect to the database."


# LOGIN ROUTE
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        
        # Check if the entered credentials are for the admin
        if email == ADMIN_EMAIL and check_password_hash(ADMIN_PASSWORD_HASH, password):
            # Simulate login for admin (assuming you have a User model and login mechanism)
            admin_user = User.query().filter_by(email=email).first()
            if admin_user:
                login_user(admin_user)
                flash('Logged in successfully as admin!', 'success')
                return redirect(url_for('admin'))
            else:
                flash('Invalid email or password', 'danger')
        else:
            # Handle regular user login
            user = User.query().filter_by(email=email).first()
            if user and user.check_password(password):
                login_user(user)
                session['user_id'] = user.user_id
                session['first_name'] = user.first_name
                session['last_name'] = user.last_name
                session['email'] = user.email
                session['age'] = user.age
                session['contact'] = user.contact
                session['username'] = user.username
                session['address'] = user.address
                flash('Logged in successfully!', 'success')
                next_page = request.args.get('next')
                return redirect(next_page or url_for('home'))
            else:
                flash('Invalid email or password', 'danger')

    return render_template('login.html', form=form, title='Login')


#LOGOUT ROUTE
@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()
    flash('You have been logged out.', 'warning')
    return redirect(url_for('home'))


# ADD AUTHORS
@app.route('/add_author', methods=['GET', 'POST'])
@login_required
def add_author():
    if current_user.username != 'admin':
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('home'))  # Redirect to home or login page

    form = AuthorForm()
    if form.validate_on_submit():
        author_name = form.author_name.data
        biography = form.biography.data
        birth_date = form.birth_date.data
        nationality = form.nationality.data
        
        # Get a connection to the database
        conn = engine.raw_connection()
        
        # Add author to the database
        add_author_to_db(conn, author_name, biography, birth_date, nationality)
        
        # Close the database connection
        conn.close()
        
        flash('Author added successfully!', 'success')
        return redirect(url_for('admin'))
    
    return render_template('add_author.html', form=form, title='Add Author')


# ADD GENRES
@app.route('/add_genre', methods=['GET', 'POST'])
@login_required
def add_genre():
    if current_user.username != 'admin':
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('home'))  # Redirect to home or login page

    form = GenreForm()  # Assuming you have a GenreForm defined for your HTML form

    if form.validate_on_submit():
        genre_name = form.genre_name.data
        description = form.description.data
        
        # Get a connection to the database
        conn = engine.raw_connection()
        
        # Add genre to the database
        add_genre_to_db(conn, genre_name, description)
        
        # Close the database connection
        conn.close()
        
        flash('Genre added successfully!', 'success')
        return redirect(url_for('admin'))  # Redirect to admin panel or another appropriate page
    
    return render_template('add_genre.html', form=form, title='Add Genre')


# ADD PUBLISHERS
@app.route('/add_publisher', methods=['GET', 'POST'])
@login_required
def add_publisher():
    if current_user.username != 'admin':
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('home'))  # Redirect to home or login page

    form = PublisherForm()  # Replace with your actual form class

    if form.validate_on_submit():
        publisher_name = form.publisher_name.data
        headquarters = form.headquarters.data
        founding_year = form.founding_year.data
        website = form.website.data
        conn = engine.raw_connection()
        # Assuming you have a function to handle database insertion
        add_publisher_to_db(conn, publisher_name, headquarters, founding_year, website)
        conn.close()
        flash('Publisher added successfully!', 'success')
        return redirect(url_for('admin'))  # Redirect to admin panel or another appropriate page
    
    return render_template('add_publisher.html', form=form, title='Add Publisher')


# ADD BOOKS
@app.route('/add_book', methods=['GET', 'POST'])
@login_required
def add_book():
    if current_user.username != 'admin':
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('home'))
    
    form = BookForm()

    # Fetch authors, genres, and publishers from the database
    conn = engine.raw_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT author_id, author_name FROM authors")
    authors = cursor.fetchall()
    form.author_id.choices = [(author[0], author[1]) for author in authors]

    cursor.execute("SELECT genre_id, genre_name FROM genre")
    genres = cursor.fetchall()
    form.genre_id.choices = [(genre[0], genre[1]) for genre in genres]

    cursor.execute("SELECT publisher_id, publisher_name FROM publishers")
    publishers = cursor.fetchall()
    form.publisher_id.choices = [(publisher[0], publisher[1]) for publisher in publishers]

    cursor.close()
    conn.close()

    if form.validate_on_submit():
        # Extract data from the form
        title = form.title.data
        author_id = form.author_id.data
        isbn = form.isbn.data
        publisher_id = form.publisher_id.data
        publication_year = form.publication_year.data
        genre_id = form.genre_id.data
        summary = form.summary.data
        language = form.language.data
        price = form.price.data
        stock = form.stock.data

        # Handle cover image upload
        cover_image = form.cover_image.data
        if cover_image and allowed_file(cover_image.filename):
            filename = secure_filename(cover_image.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            cover_image.save(file_path)
            cover_image_path = file_path.replace('\\', '/')  # Replace backslashes with forward slashes
        else:
            cover_image_path = None  # Or handle error condition

        # Add book to the database
        conn = engine.raw_connection()
        add_book_to_db(conn, title, author_id, isbn, publisher_id, publication_year,
                       genre_id, summary, language, price, stock, cover_image_path)
        conn.close()

        flash('Book added successfully!', 'success')
        return redirect(url_for('admin'))

    # Render the add_book.html template with the form
    return render_template('add_book.html', form=form, title='Add Book')


# GET THE DETAILS OF THE SELECTED BOOK
@app.route('/book/<int:book_id>', methods=['GET', 'POST'])
def book_details(book_id):
    conn = create_db_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)

        # Query to fetch book details and average rating
        book_query = """
            SELECT b.book_id, b.title, a.author_name, g.genre_name, p.publisher_name, b.price,
                   b.publication_year, b.isbn, b.summary, b.language, b.stock, b.cover_image,
                   AVG(s.stars) AS avg_rating
            FROM books b
            INNER JOIN authors a ON b.author_id = a.author_id
            INNER JOIN genre g ON b.genre_id = g.genre_id
            INNER JOIN publishers p ON b.publisher_id = p.publisher_id
            LEFT JOIN stars s ON b.book_id = s.book_id
            WHERE b.book_id = %s
            GROUP BY b.book_id
        """

        # Query to fetch recent 5 reviews for the book
        recent_reviews_query = """
            SELECT r.content, u.username
            FROM reviews r
            INNER JOIN users u ON r.user_id = u.user_id
            WHERE r.book_id = %s
            ORDER BY r.review_date DESC
            LIMIT 5
        """

        # Query to fetch all reviews for the book
        all_reviews_query = """
            SELECT r.content, u.username
            FROM reviews r
            INNER JOIN users u ON r.user_id = u.user_id
            WHERE r.book_id = %s
            ORDER BY r.review_date DESC
        """

        if request.method == 'POST':
            if not current_user.is_authenticated:
                flash('You must be logged in to add a review or rate the book.', 'warning')
                return redirect(url_for('login'))  # Redirect to login page if user is not logged in

            if 'rating' in request.form:
                rating = int(request.form['rating'])
                try:
                    query = """
                        INSERT INTO stars (book_id, user_id, stars, star_date)
                        VALUES (%s, %s, %s, %s)
                    """
                    user_id = current_user.user_id  # Fetch user ID from Flask-Login's current_user

                    # Execute the query with current date
                    cursor.execute(query, (book_id, user_id, rating, date.today()))
                    conn.commit()

                    flash('Rating added successfully!', 'success')
                    return redirect(url_for('book_details', book_id=book_id))

                except Exception as e:
                    conn.rollback()
                    flash(f'Error adding rating', 'danger')
                    return redirect(url_for('book_details', book_id=book_id))

            elif 'review' in request.form:
                form = ReviewForm(request.form)
                if form.validate():
                    # Extract review content from form
                    review_content = form.content.data.strip()

                    # Calculate polarity using TextBlob
                    polarity = analyze_sentiment(review_content)

                    # Insert the review into the database
                    try:
                        query = """
                            INSERT INTO reviews (content, user_id, book_id, polarity, review_date)
                            VALUES (%s, %s, %s, %s, %s)
                        """
                        user_id = current_user.user_id  # Fetch user ID from Flask-Login's current_user

                        # Execute the query with current date
                        cursor.execute(query, (review_content, user_id, book_id, polarity, date.today()))
                        conn.commit()

                        flash('Review added successfully!', 'success')
                        conn.close()
                        return redirect(url_for('book_details', book_id=book_id))

                    except Exception as e:
                        conn.rollback()
                        flash(f'Error adding review', 'danger')
                        conn.close()
                        return redirect(url_for('book_details', book_id=book_id))

                else:
                    flash('Invalid form data. Please check your inputs.', 'danger')
                    conn.close()
                    return redirect(url_for('book_details', book_id=book_id))

        else:
            # Handle GET request to fetch book details and reviews
            try:
                # Execute book query
                cursor.execute(book_query, (book_id,))
                book = cursor.fetchone()

                if book:
                    # Execute recent reviews query
                    cursor.execute(recent_reviews_query, (book_id,))
                    recent_reviews = cursor.fetchall()

                    # Execute all reviews query (for viewing all reviews link)
                    cursor.execute(all_reviews_query, (book_id,))
                    all_reviews = cursor.fetchall()

                    conn.close()

                    return render_template('book_details.html', book=book, recent_reviews=recent_reviews, all_reviews=all_reviews, review_form=ReviewForm(), rating_form=StarRatingForm())

                else:
                    flash('Book not found!', 'danger')
                    conn.close()
                    return redirect(url_for('home'))

            except Exception as e:
                flash(f"Error fetching book details", 'danger')
                conn.close()
                return redirect(url_for('home'))

    else:
        flash("Failed to connect to the database.", 'danger')
        return redirect(url_for('home'))


# ADD TO CART
@app.route('/add_to_cart/<int:book_id>', methods=['POST'])
@login_required
def add_to_cart(book_id):
    # print("Book id")
    # print(book_id)
    # Validate and process the request
    if request.method == 'POST':
        # Check if the book is already in the cart for the current user
        conn = create_db_connection()
        if conn:
            cursor = conn.cursor()
            
            # Check if the book is already in the user's cart
            cursor.execute("SELECT * FROM carts WHERE user_id = %s AND book_id = %s", (current_user.user_id, book_id))
            existing_cart_item = cursor.fetchone()
            
            if existing_cart_item:
                # If the book already exists in the cart, notify the user and redirect
                flash('This book is already in your cart.', 'info')
                conn.close()
                return redirect(url_for('book_details', book_id=book_id))
            
            try:
                # Insert the item into the cart table
                cart_date = date.today()
                
                # Insert into the carts table with default quantity of 1
                cursor.execute("""
                    INSERT INTO carts (user_id, book_id, cart_date, quantity)
                    VALUES (%s, %s, %s, 1)
                """, (current_user.user_id, book_id, cart_date))
                
                conn.commit()
                conn.close()
                
                # Flash message for successful addition
                flash('Book added to cart successfully.', 'success')
                return redirect(url_for('my_cart', user_id = current_user.user_id, username = current_user.username))
            
            except Exception as e:
                # Handle database errors
                flash(f'Error adding book to cart', 'danger')
                conn.close()
                return redirect(url_for('book_details', book_id=book_id))
        
        else:
            flash('Failed to connect to the database.', 'danger')
            return redirect(url_for('book_details', book_id=book_id))

    else:
        # Handle other HTTP methods (GET, etc.) if necessary
        return redirect(url_for('home'))


# GET ORDER SUMMARY AFTER PLACING ORDER
@app.route('/order_summary/<int:order_id>')
@login_required
def order_summary(order_id):
    print(order_id)
    try:
        conn = create_db_connection()
        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT orders.order_id, orders.quantity, orders.date_placed, orders.total_amount, 
                   orders.status, orders.payment_method, 
                   books.title as title, books.price as price, books.cover_image as cover_image, 
                   authors.author_name as author_name, 
                   genre.genre_name as genre_name, 
                   publishers.publisher_name as publisher_name
            FROM orders
            JOIN books ON orders.book_id = books.book_id
            JOIN authors ON books.author_id = authors.author_id
            JOIN genre ON books.genre_id = genre.genre_id
            JOIN publishers ON books.publisher_id = publishers.publisher_id
            WHERE orders.order_id = %s AND orders.user_id = %s
        """
        cursor.execute(query, (order_id, current_user.user_id))
        order = cursor.fetchone()

        query = """
            SELECT transaction_id FROM transactions WHERE %s = transactions.transaction_id
        """
        cursor.execute(query, (order_id,))
        transaction_id = cursor.fetchone()


        if(not transaction_id) :
            transaction_id = ""

        if not order:
            return "Order not found for this user."

        # Debugging: print order details
        print("sumarry order")
        print(order)

        return render_template('order_summary.html', order=order, transaction_id=transaction_id)

    except Exception as e:
        # Log the exception for further investigation
        flash(f"Error fetching order details", 'danger')
        return "Error fetching order details. Please try again later.", 500  # HTTP 500 Internal Server Error

    finally:
        if 'conn' in locals() and conn:
            conn.close()




# ADMIN VIEW OF BOOKS 
@app.route('/admin/books')
@login_required
def admin_books():
    logging.debug("Inside admin_books route.")
    if current_user.is_authenticated:
        logging.debug(f"Current user: {current_user}")
        logging.debug(f"Current user email: {current_user.email}")
        logging.debug(f"Admin email: {ADMIN_EMAIL}")
        if current_user.email == ADMIN_EMAIL:
            try:
                conn = create_db_connection()
                if conn:
                    cursor = conn.cursor(dictionary=True)
                    try:
                        cursor.execute("""
                            SELECT b.book_id, b.title, b.price, b.stock, a.author_name, g.genre_name, p.publisher_name
                            FROM books b
                            INNER JOIN authors a ON b.author_id = a.author_id
                            INNER JOIN genre g ON b.genre_id = g.genre_id
                            INNER JOIN publishers p ON b.publisher_id = p.publisher_id
                        """)
                        books = cursor.fetchall()
                        conn.close()
                        logging.debug(f"Fetched books: {books}")
                        return render_template('admin_books.html', books=books)
                    except Exception as e:
                        conn.close()
                        logging.error(f"Error fetching books: ")
                        flash(f"Error fetching books", 'danger')
                else:
                    logging.error("Failed to connect to the database.")
                    flash("Failed to connect to the database.", 'danger')
            except Exception as e:
                logging.error(f"Error creating database connection")
                flash(f"Error creating database connection", 'danger')
        else:
            logging.debug("Unauthorized access. Only admin can access this page.")
            flash("Unauthorized access. Only admin can access this page.", 'danger')
    else:
        logging.debug("User is not authenticated. Please log in.")
        flash("User is not authenticated. Please log in.", 'danger')

    return redirect(url_for('home'))  # Redirect to home page if not admin or on error


# EDIT BOOK DETAILS
@app.route('/edit_book/<int:book_id>', methods=['GET', 'POST'])
@login_required
def edit_book(book_id):
    if current_user.username != 'admin':
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('home'))
    
    form = EditBookForm()

    # Fetch existing book details from the database
    conn = engine.raw_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT title, author_id, isbn, publisher_id, publication_year,
               genre_id, summary, language, price, stock, cover_image
        FROM books
        WHERE book_id = %s
    """, (book_id,))
    book_data = cursor.fetchone()
    cursor.close()
    conn.close()

    if book_data:
        form.title.data = book_data[0]  # title
        form.author_id.data = book_data[1]  # author_id
        form.isbn.data = book_data[2]  # isbn
        form.publisher_id.data = book_data[3]  # publisher_id
        form.publication_year.data = book_data[4]  # publication_year
        form.genre_id.data = book_data[5]  # genre_id
        form.summary.data = book_data[6]  # summary
        form.language.data = book_data[7]  # language
        form.price.data = book_data[8]  # price
        form.stock.data = book_data[9]  # stock
        # Set cover image field to the existing image path (for display)
        form.cover_image.current_cover_image = book_data[10]  # cover_image_path

    # Populate dropdowns with data from the database
    conn = engine.raw_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT author_id, author_name FROM authors")
    authors = cursor.fetchall()
    form.author_id.choices = [(author[0], author[1]) for author in authors]

    cursor.execute("SELECT genre_id, genre_name FROM genre")
    genres = cursor.fetchall()
    form.genre_id.choices = [(genre[0], genre[1]) for genre in genres]

    cursor.execute("SELECT publisher_id, publisher_name FROM publishers")
    publishers = cursor.fetchall()
    form.publisher_id.choices = [(publisher[0], publisher[1]) for publisher in publishers]

    cursor.close()
    conn.close()

    if form.validate_on_submit():
        # Extract data from the form
        title = form.title.data
        author_id = form.author_id.data
        isbn = form.isbn.data
        publisher_id = form.publisher_id.data
        publication_year = form.publication_year.data
        genre_id = form.genre_id.data
        summary = form.summary.data
        language = form.language.data
        price = form.price.data
        stock = form.stock.data

        # Handle cover image upload/update
        if form.cover_image.data:
            cover_image = form.cover_image.data
            if allowed_file(cover_image.filename):
                filename = secure_filename(cover_image.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                cover_image.save(file_path)
                cover_image_path = file_path.replace('\\', '/')  # Replace backslashes with forward slashes
            else:
                flash('Invalid file type for cover image.', 'danger')
                return redirect(url_for('edit_book', book_id=book_id))
        else:
            # Use existing cover image path if no new image is uploaded
            cover_image_path = book_data[10]  # cover_image_path

        # Update book in the database
        conn = engine.raw_connection()
        update_book_in_db(conn, book_id, title, author_id, isbn, publisher_id, publication_year,
                          genre_id, summary, language, price, stock, cover_image_path)
        conn.close()

        flash('Book details updated successfully!', 'success')
        return redirect(url_for('admin_books'))  # Redirect to admin books page after update

    # Render edit_book.html template with populated form
    return render_template('edit_book.html', form=form, book_id=book_id)


# GET BOOK DETAILS 
@app.route('/admin/book/<int:book_id>')
@login_required
def admin_book_details(book_id):
    if current_user.is_authenticated and current_user.email == ADMIN_EMAIL:
        conn = create_db_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)

            # Query to fetch book details and average rating
            book_query = """
                SELECT b.title, a.author_name, g.genre_name, p.publisher_name, b.price,
                       b.publication_year, b.isbn, b.summary, b.language, b.stock, b.cover_image,
                       AVG(s.stars) AS avg_rating
                FROM books b
                INNER JOIN authors a ON b.author_id = a.author_id
                INNER JOIN genre g ON b.genre_id = g.genre_id
                INNER JOIN publishers p ON b.publisher_id = p.publisher_id
                LEFT JOIN stars s ON b.book_id = s.book_id
                WHERE b.book_id = %s
                GROUP BY b.book_id
            """
            
            # Query to fetch reviews for the book
            reviews_query = """
                SELECT r.content, u.username
                FROM reviews r
                INNER JOIN users u ON r.user_id = u.user_id
                WHERE r.book_id = %s
            """

            try:
                # Execute book query
                cursor.execute(book_query, (book_id,))
                book = cursor.fetchone()

                if book:
                    # Execute reviews query
                    cursor.execute(reviews_query, (book_id,))
                    reviews = cursor.fetchall()

                    conn.close()

                    # Create a dictionary to pass to the template
                    book_details = {
                        'title': book['title'],
                        'author_name': book['author_name'],
                        'genre_name': book['genre_name'],
                        'publisher_name': book['publisher_name'],
                        'price': book['price'],
                        'publication_year': book['publication_year'],
                        'isbn': book['isbn'],
                        'ummary': book['summary'],
                        'language': book['language'],
                        'tock': book['stock'],
                        'cover_image': book['cover_image'],
                        'avg_rating': book['avg_rating']
                    }

                    return render_template('admin_book_details.html', book=book_details, reviews=reviews)
                else:
                    flash('Book not found!', 'danger')
                    conn.close()
                    return render_template('home.html')

            except Exception as e:
                flash(f"Error fetching book details", 'danger')
                conn.close()
                return render_template('home.html')

        else:
            flash("Failed to connect to the database.", 'danger')
            return render_template('admin.html')

    else:
        flash("Unauthorized access. Only admin can access this page.", 'danger')
        return redirect(url_for('home'))


# VIEW LIST OF ALL AUTHORS 
@app.route('/authors')
@login_required
def all_authors():
    if current_user.is_authenticated:
        if current_user.email == ADMIN_EMAIL:
            conn = create_db_connection()
            if conn:
                cursor = conn.cursor(dictionary=True)

                try:
                    # Query to fetch all authors
                    cursor.execute("SELECT * FROM authors")
                    authors = cursor.fetchall()

                    conn.close()
                    return render_template('all_authors.html', authors=authors, ADMIN_EMAIL = ADMIN_EMAIL)

                except Exception as e:
                    flash(f"Error fetching authors", 'danger')
                    conn.close()

            else:
                flash("Failed to connect to the database.", 'danger')

        else:
            flash("Unauthorized access. Only admins can view authors.", 'danger')

    else:
        flash("User is not authenticated. Please log in.", 'danger')

    return redirect(url_for('home'))  # Redirect to home page on error or unauthorized access



# CHECK IF THE CARD NUMBER IS VALID
def simulate_card_payment(card_number, cvv, expiry, amount):
    if len(card_number) == 16 and len(cvv) == 3 and len(expiry) == 5 and expiry[2] == '/':
        return True, ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))
    return False, None



# PLACE ORDER
@app.route('/place_order/<int:book_id>', methods=['GET', 'POST'])
@login_required
def place_order(book_id):
    conn = create_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT * FROM books WHERE book_id = %s", (book_id,))
    book = cursor.fetchone()

    if request.method == 'POST':
        quantity = int(request.form['quantity'])
        total_amount = quantity * book['price']
        payment_method = request.form['payment_method']
        print(f"Quantity: {quantity}")
        print(f"Total Amount: {total_amount}")
        print(f"Payment Method: {payment_method}")
        delivered_status = True

        if payment_method == 'card':
            return redirect(url_for('payment', book_id=book_id, quantity=quantity, total_amount=total_amount))

        elif payment_method == 'cash':
            try:
                # Check if sufficient stock is available
                if quantity <= book['stock']:
                    # Proceed with placing the order
                    cursor.execute("""
                        INSERT INTO orders (user_id, book_id, quantity, date_placed, total_amount, status, payment_method)
                        VALUES (%s, %s, %s, CURDATE(), %s, 'Placed', %s)
                    """, (current_user.user_id, book_id, quantity, total_amount, payment_method))
                    
                    order_id = cursor.lastrowid
                    cursor.execute("DELETE FROM carts WHERE user_id = %s AND book_id = %s", (current_user.user_id, book_id))
                    
                    # Decrement the stock of the book
                    new_stock = book['stock'] - quantity
                    cursor.execute("UPDATE books SET stock = %s WHERE book_id = %s", (new_stock, book_id))
                    
                    conn.commit()
                    print(f"Order placed for Order ID: {order_id}")
                    conn.close()

                    return redirect(url_for('order_summary', order_id=order_id))
                else:
                    flash("Insufficient stock available for this book.", 'danger')
                    conn.close()
                    return redirect(url_for('place_order', book_id=book_id))  # Redirect back to place_order page if insufficient stock

            except Exception as e:
                conn.rollback()
                flash(f"Transaction failed", 'danger')
                print(f"Transaction failed")
                conn.close()
        else:
            flash("Invalid payment method selected", 'danger')
            conn.close()
            return redirect(url_for('place_order', book_id=book_id))  # Redirect back to place_order page if payment method is invalid
    
    return render_template('place_order.html', book=book, user=current_user)



# PAYMENT ROUTE (CARD)
@app.route('/payment/<int:book_id>/<int:quantity>/<float:total_amount>', methods=['GET', 'POST'])
@login_required
def payment(book_id, quantity, total_amount):
    if request.method == 'POST':
        card_number = request.form['card_number']
        cvv = request.form['cvv']
        expiry_month = request.form['expiry_month']
        expiry_year = request.form['expiry_year']
        expiry = f"{expiry_month}/{expiry_year[-2:]}"  # Combine to form MM/YY format

        print(f"Card Number: {card_number}")
        print(f"CVV: {cvv}")
        print(f"Expiry: {expiry}")

        # Check if requested quantity exceeds available stock
        conn = create_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT stock FROM books WHERE book_id = %s", (book_id,))
        book_stock = cursor.fetchone()['stock']
        conn.close()

        if quantity > book_stock:
            flash('Requested quantity exceeds available stock.', 'danger')
            return redirect(url_for('place_order', book_id=book_id))

        payment_success, transaction_id = simulate_card_payment(card_number, cvv, expiry, total_amount)
        
        if payment_success:
            print(f"Payment successful, Transaction ID: {transaction_id}")
            conn = create_db_connection()
            cursor = conn.cursor(dictionary=True)
            try:
                conn.start_transaction()
                cursor.execute("""
                    INSERT INTO orders (user_id, book_id, quantity, date_placed, total_amount, status, payment_method)
                    VALUES (%s, %s, %s, CURDATE(), %s, 'Placed', 'card')
                """, (current_user.user_id, book_id, quantity, total_amount))
                
                order_id = cursor.lastrowid
                cursor.execute("""
                    INSERT INTO transactions (transaction_id, user_id, order_id, total_amount)
                    VALUES (%s, %s, %s, %s)
                """, (transaction_id, current_user.user_id, order_id, total_amount))
                cursor.execute("DELETE FROM carts WHERE user_id = %s AND book_id = %s", (current_user.user_id, book_id))
                
                # Decrement the stock of the book
                new_stock = book_stock - quantity
                cursor.execute("UPDATE books SET stock = %s WHERE book_id = %s", (new_stock, book_id))
                
                conn.commit()
                print(f"Order placed and transaction logged for Order ID: {order_id}")
                conn.close()

                return redirect(url_for('order_summary', order_id=order_id))

            
            except Exception as e:
                conn.rollback()
                flash(f"Transaction failed", 'danger')
                print(f"Transaction failed")
                conn.close()
        
        else:
            flash('Payment failed. Please check your card details and try again.', 'danger')
            print("Payment failed.")
    
    return render_template('payment.html')


# VIEW USER 
@app.route('/myprofile/<username>/<int:user_id>', methods=['GET'])
@login_required
def my_profile(username, user_id):
    if current_user.username == username and current_user.user_id == user_id:
        conn = create_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT user_id, username, first_name, last_name, email, age, contact, address 
                FROM users WHERE user_id = %s
            """, (user_id,))
            user = cursor.fetchone()

            if user:
                user_dict = {
                    'user_id': user[0],
                    'username': user[1],
                    'first_name': user[2],
                    'last_name': user[3],
                    'email': user[4],
                    'age': user[5],
                    'contact': user[6],
                    'address': user[7]
                }
                return render_template('my_profile.html', user=user_dict)
            else:
                flash('User not found.', 'danger')
                return redirect(url_for('home'))

        except Exception as e:
            flash(f'Error fetching user details', 'danger')
            return redirect(url_for('home'))

        finally:
            cursor.close()
            conn.close()

    else:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('home'))


# EDIT USER PROFILE
@app.route('/edit_profile/<username>/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_profile(username, user_id):
    if current_user.username == username and current_user.user_id == user_id:
        conn = create_db_connection()
        cursor = conn.cursor()

        if request.method == 'POST':
            first_name = request.form['first_name']
            last_name = request.form['last_name']
            email = request.form['email']
            age = request.form['age']
            contact = request.form['contact']
            address = request.form['address']

            try:
                cursor.execute("""
                    UPDATE users SET 
                    first_name = %s, 
                    last_name = %s, 
                    email = %s, 
                    age = %s, 
                    contact = %s, 
                    address = %s 
                    WHERE user_id = %s
                """, (first_name, last_name, email, age, contact, address, current_user.user_id))
                conn.commit()
                flash('Profile updated successfully.', 'success')
                return redirect(url_for('my_profile', username=current_user.username, user_id=current_user.user_id))
            except Exception as e:
                conn.rollback()
                flash(f'Error updating profile', 'danger')
            finally:
                cursor.close()
                conn.close()

        # Fetch existing user data for prefilling the form
        cursor.execute("""
            SELECT user_id, username, first_name, last_name, email, age, contact, address 
            FROM users WHERE user_id = %s
        """, (current_user.user_id,))
        user = cursor.fetchone()
        cursor.close()

        if user:
            user_dict = {
                'user_id': user[0],
                'username': user[1],
                'first_name': user[2],
                'last_name': user[3],
                'email': user[4],
                'age': user[5],
                'contact': user[6],
                'address': user[7]
            }
            return render_template('edit_profile.html', user=user_dict)
        else:
            flash('User not found.', 'danger')
            return redirect(url_for('home'))

    else:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('home'))


# EDIT PASSWORD
@app.route('/edit_password/<username>/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_password(username, user_id):
    if current_user.username == username and current_user.user_id == user_id:
        if request.method == 'POST':
            current_password = request.form['current_password']
            new_password = request.form['new_password']
            confirm_password = request.form['confirm_password']

            if new_password != confirm_password:
                flash('New passwords do not match.', 'danger')
                return redirect(url_for('edit_password', username=username, user_id=user_id))

            conn = create_db_connection()
            cursor = conn.cursor()

            try:
                cursor.execute("SELECT password FROM users WHERE user_id = %s", (user_id,))
                stored_password = cursor.fetchone()[0]

                if check_password_hash(stored_password, current_password):
                    hashed_password = generate_password_hash(new_password)
                    cursor.execute("UPDATE users SET password = %s WHERE user_id = %s", (hashed_password, user_id))
                    conn.commit()
                    flash('Password updated successfully.', 'success')
                    return redirect(url_for('my_profile', username=username, user_id=user_id))
                else:
                    flash('Current password is incorrect.', 'danger')
                    return redirect(url_for('edit_password', username=username, user_id=user_id))

            except Exception as e:
                conn.rollback()
                flash(f'Error updating password', 'danger')
            finally:
                cursor.close()
                conn.close()

        return render_template('edit_password.html', username=username, user_id=user_id)
    else:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('home'))


# USER CARTS 
@app.route('/my_cart/<username>/<int:user_id>', methods=['GET'])
@login_required
def my_cart(username, user_id):
    if current_user.username == username and current_user.user_id == user_id:
        conn = create_db_connection()
        cursor = conn.cursor(dictionary=True)

        try:
            # Fetch cart items for the current user
            cursor.execute("""
                SELECT c.cart_id, b.book_id, b.title, b.author_id, c.quantity, b.price, b.cover_image
                FROM carts c
                JOIN books b ON c.book_id = b.book_id
                WHERE c.user_id = %s
            """, (user_id,))
            cart_items = cursor.fetchall()

            # Convert fetched data to a list of dictionaries
            cart_items_list = []
            for item in cart_items:
                cart_items_list.append({
                    'cart_id': item['cart_id'],
                    'book_id': item['book_id'],
                    'title': item['title'],
                    'author_id': item['author_id'],
                    'quantity': item['quantity'],
                    'price': item['price'],
                    'cover_image': item['cover_image']
                })

            return render_template('my_cart.html', cart_items=cart_items_list)
        
        except Exception as e:
            flash(f'Error fetching cart details', 'danger')
            return redirect(url_for('home'))  # Redirect to home page on error
        
        finally:
            cursor.close()
            conn.close()

    else:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('home'))  # Redirect to home page if unauthorized


# REMOVE ITEM FROM CART
@app.route('/remove_from_cart/<int:cart_id>', methods=['POST'])
@login_required
def remove_from_cart(cart_id):
    conn = create_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT user_id FROM carts WHERE cart_id = %s", (cart_id,))
        cart_item = cursor.fetchone()

        if cart_item and cart_item[0] == current_user.user_id:
            cursor.execute("DELETE FROM carts WHERE cart_id = %s", (cart_id,))
            conn.commit()
            flash('Item removed from cart.', 'info')
        else:
            flash('Unauthorized access.', 'danger')

        return redirect(url_for('my_cart', username=current_user.username, user_id=current_user.user_id))
    except Exception as e:
        conn.rollback()
        flash(f'Error removing item from cart', 'danger')
        return redirect(url_for('my_cart', username=current_user.username, user_id=current_user.user_id))
    finally:
        cursor.close()
        conn.close()


# VIEW THE REVIEWS MADE BY THE PARTICULAR USER 
@app.route('/my_reviews/<username>/<int:user_id>', methods=['GET'])
@login_required
def my_reviews(username, user_id):
    if current_user.username == username and current_user.user_id == user_id:
        conn = create_db_connection()
        cursor = conn.cursor()

        try:
            # Fetch reviews authored by the current user
            cursor.execute("""
                SELECT r.review_id, r.content, r.review_date, b.title
                FROM reviews r
                JOIN books b ON r.book_id = b.book_id
                WHERE r.user_id = %s
            """, (user_id,))
            reviews = cursor.fetchall()

            # Convert fetched data to a list of dictionaries
            reviews_list = []
            for review in reviews:
                reviews_list.append({
                    'review_id': review[0],
                    'content': review[1],
                    'review_date': review[2],
                    'book_title': review[3]
                })

            return render_template('my_reviews.html', reviews=reviews_list)
        except Exception as e:
            flash(f'Error fetching reviews', 'danger')
            return redirect(url_for('home'))
        finally:
            cursor.close()
            conn.close()
    else:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('home'))
  

# CANCEL ORDER
@app.route('/cancel_order/<int:order_id>', methods=['POST'])
@login_required
def cancel_order(order_id):
    conn = create_db_connection()
    cursor = conn.cursor()

    try:
        # Fetch transaction details for the order
        cursor.execute("SELECT * FROM transactions WHERE order_id = %s", (order_id,))
        transaction = cursor.fetchone()


        # Delete the transaction associated with the order
        cursor.execute("DELETE FROM transactions WHERE order_id = %s", (order_id,))
        conn.commit()

        # Fetch order details including book_id and quantity
        cursor.execute("SELECT book_id, quantity FROM orders WHERE order_id = %s AND user_id = %s", (order_id, current_user.user_id))
        order_data = cursor.fetchone()

        if not order_data:
            flash('Order not found or you are not authorized to cancel this order.', 'danger')
            return redirect(url_for('orders'))

        book_id = order_data[0]  # accessing the first element (book_id) in the tuple
        cancelled_quantity = order_data[1]  # accessing the second element (quantity) in the tuple

        # Delete the order
        cursor.execute("DELETE FROM orders WHERE order_id = %s", (order_id,))
        conn.commit()

        # Increase stock of the book
        cursor.execute("UPDATE books SET stock = stock + %s WHERE book_id = %s", (cancelled_quantity, book_id))
        conn.commit()

        flash('Order cancelled successfully. Quantity returned to stock.', 'success')

    except Exception as e:
        conn.rollback()
        flash(f'Error cancelling order', 'danger')

    finally:
        conn.close()

    return redirect(url_for('orders', username=current_user.username, user_id=current_user.user_id))


# VIEW ORDERS MADE BY A PARTICULAR USER 
@app.route('/orders/<username>/<int:user_id>', methods=['GET'])
@login_required  # Enforces login requirement
def orders(username, user_id):
    if current_user.username == username and current_user.user_id == user_id:
        conn = create_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Fetch orders placed by the logged-in user
        query = """
            SELECT orders.order_id, orders.quantity, orders.date_placed, orders.total_amount,
                   orders.status, orders.payment_method, 
                   books.title, books.price, books.cover_image, 
                   authors.author_name, 
                   genre.genre_name, 
                   publishers.publisher_name
            FROM orders
            JOIN books ON orders.book_id = books.book_id
            JOIN authors ON books.author_id = authors.author_id
            JOIN genre ON books.genre_id = genre.genre_id
            JOIN publishers ON books.publisher_id = publishers.publisher_id
            WHERE orders.user_id = %s
            ORDER BY orders.date_placed DESC
        """
        cursor.execute(query, (current_user.user_id,))
        orders = cursor.fetchall()
        conn.close()

        return render_template('orders.html', orders=orders)
    else:
        abort(403)  # If user is not authenticated or user IDs don't match, deny access


# FETCH ALL GENRES 
@app.route('/genres')
@login_required
def all_genres():
    if current_user.is_authenticated:
        if current_user.email == ADMIN_EMAIL:
            conn = create_db_connection()
            if conn:
                cursor = conn.cursor(dictionary=True)

                try:
                    # Query to fetch all genres
                    cursor.execute("SELECT * FROM genre")
                    genres = cursor.fetchall()

                    conn.close()
                    return render_template('all_genres.html', genres=genres, ADMIN_EMAIL=ADMIN_EMAIL)

                except Exception as e:
                    flash(f"Error fetching genres", 'danger')
                    conn.close()

            else:
                flash("Failed to connect to the database.", 'danger')

        else:
            flash("Unauthorized access. Only admins can view genres.", 'danger')

    else:
        flash("User is not authenticated. Please log in.", 'danger')

    return redirect(url_for('home'))


@app.route('/publishers')
@login_required
def all_publishers():
    if current_user.is_authenticated:
        # Assuming current_user.email == ADMIN_EMAIL for admin check
        if current_user.email == ADMIN_EMAIL:
            conn = create_db_connection()
            if conn:
                cursor = conn.cursor(dictionary=True)

                try:
                    # Query to fetch all publishers
                    cursor.execute("SELECT * FROM publishers")
                    publishers = cursor.fetchall()

                    conn.close()
                    return render_template('all_publishers.html', publishers=publishers, ADMIN_EMAIL=ADMIN_EMAIL)

                except Exception as e:
                    flash(f"Error fetching publishers", 'danger')
                    conn.close()

            else:
                flash("Failed to connect to the database.", 'danger')

        else:
            flash("Unauthorized access. Only admins can view publishers.", 'danger')

    else:
        flash("User is not authenticated. Please log in.", 'danger')

    return redirect(url_for('home'))



@app.route('/update_order_status', methods=['GET', 'POST'])
@login_required
def update_order_status():
    if current_user.is_authenticated and current_user.email == ADMIN_EMAIL:
        if request.method == 'POST':
            order_id = request.form['order_id']
            new_status = request.form['new_status']
            
            conn = create_db_connection()
            cursor = conn.cursor(dictionary=True)  # Use dictionary cursor for easier access

            try:
                # Fetch current status of the order
                cursor.execute("SELECT * FROM orders WHERE order_id = %s", (order_id,))
                order_data = cursor.fetchone()

                if not order_data:
                    flash('Order not found for the provided ID.', 'danger')
                else:
                    current_status = order_data['status']
                    book_id = order_data['book_id']
                    quantity = order_data['quantity']

                    if new_status == 'Delivered' and current_status == 'Placed':
                        # Update the order status to 'Delivered'
                        cursor.execute("""
                            UPDATE orders
                            SET status = 'Delivered'
                            WHERE order_id = %s
                        """, (order_id,))

                        conn.commit()
                        flash('Order status updated to Delivered successfully.', 'success')

                    elif new_status == 'Returned' and current_status == 'Delivered':
                        # Update the order status to 'Returned'
                        cursor.execute("""
                            UPDATE orders
                            SET status = 'Returned'
                            WHERE order_id = %s
                        """, (order_id,))

                        # Update the stocks in the books table
                        cursor.execute("""
                            UPDATE books
                            SET stock = stock + %s
                            WHERE book_id = %s
                        """, (quantity, book_id))

                        conn.commit()
                        flash('Order status updated to Returned successfully.', 'success')

                    else:
                        flash(f'Invalid status transition: Cannot update from {current_status} to {new_status}.', 'danger')

                conn.close()

                return redirect(url_for('admin'))

            except Exception as e:
                conn.rollback()
                flash(f"Failed to update order status", 'danger')
                print(f"Failed to update order status")
                conn.close()

        return render_template('update_order_status.html')
    else:
        flash("Unauthorized access. Only admins can update order status.", 'danger')
        return redirect(url_for('home'))  # Redirect to home page if not admin



@app.errorhandler(403)
def forbidden(error):
    return render_template('403.html'), 403


@app.errorhandler(Unauthorized)
def handle_unauthorized_error(e):
    flash("Please log in to access this page.", "info")
    return redirect(url_for("login"))  # Redirect to the login page


@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404

if __name__ == "__main__":
    app.run(debug=True)
