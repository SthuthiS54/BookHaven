import mysql.connector as MySQL
from mysql.connector import Error

def create_db_connection():
    try:
        # Establish a connection to the database
        conn = MySQL.connect(
            host="localhost",
            user="root",
            password="mysqlpassword",
            database="bookhaven"
        )

        # Check if connection is successful
        if conn.is_connected():
            print("Connected to MySQL database")
            return conn

    except Error as e:
        print("Error connecting to MySQL database:", e)

    return None

def create_tables(conn):
    cursor = conn.cursor()

    # Define table creation queries in a list
    tables = [
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id INT NOT NULL AUTO_INCREMENT,
            first_name VARCHAR(100) NOT NULL,
            last_name VARCHAR(100) NOT NULL,
            email VARCHAR(255) NOT NULL UNIQUE,
            age INT,
            contact VARCHAR(20),
            username VARCHAR(50) NOT NULL UNIQUE,
            address VARCHAR(255),
            password VARCHAR(255) NOT NULL,
            PRIMARY KEY (user_id)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS authors (
            author_id INT NOT NULL AUTO_INCREMENT,
            author_name VARCHAR(255) NOT NULL,
            biography TEXT,
            birth_date DATE,
            nationality VARCHAR(100),
            PRIMARY KEY (author_id)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS genre (
            genre_id INT NOT NULL AUTO_INCREMENT,
            genre_name VARCHAR(100) NOT NULL,
            description TEXT,
            PRIMARY KEY (genre_id),
            UNIQUE KEY (genre_name)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS publishers (
            publisher_id INT NOT NULL AUTO_INCREMENT,
            publisher_name VARCHAR(255) NOT NULL,
            headquarters VARCHAR(255),
            founding_year YEAR,
            website VARCHAR(255),
            PRIMARY KEY (publisher_id),
            UNIQUE KEY (publisher_name)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS books (
            book_id INT NOT NULL AUTO_INCREMENT,
            title VARCHAR(255) NOT NULL,
            author_id INT,
            isbn VARCHAR(20),
            publisher_id INT,
            publication_year INT,
            genre_id INT,
            summary TEXT,
            language VARCHAR(50),
            price DECIMAL(10,2),
            stock INT,
            cover_image VARCHAR(255),
            PRIMARY KEY (book_id),
            FOREIGN KEY (author_id) REFERENCES authors(author_id),
            FOREIGN KEY (genre_id) REFERENCES genre(genre_id),
            FOREIGN KEY (publisher_id) REFERENCES publishers(publisher_id)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS publications (
            publication_id INT NOT NULL AUTO_INCREMENT,
            publication_name VARCHAR(255) NOT NULL,
            city VARCHAR(100),
            country VARCHAR(100),
            established_year YEAR,
            website VARCHAR(255),
            PRIMARY KEY (publication_id),
            UNIQUE KEY (publication_name)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS reviews (
            review_id INT NOT NULL AUTO_INCREMENT,
            content TEXT NOT NULL,
            user_id INT NOT NULL,
            book_id INT NOT NULL,
            polarity VARCHAR(20),
            review_date DATE NOT NULL,
            PRIMARY KEY (review_id),
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (book_id) REFERENCES books(book_id)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS stars (
            book_id INT NOT NULL,
            user_id INT NOT NULL,
            stars INT NOT NULL,
            star_date DATE NOT NULL,
            PRIMARY KEY (book_id, user_id),
            FOREIGN KEY (book_id) REFERENCES books(book_id),
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS carts (
            cart_id INT NOT NULL AUTO_INCREMENT,
            user_id INT NOT NULL,
            book_id INT NOT NULL,
            cart_date DATE NOT NULL,
            quantity INT NOT NULL,
            PRIMARY KEY (cart_id),
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (book_id) REFERENCES books(book_id)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS orders (
            order_id INT NOT NULL AUTO_INCREMENT,
            user_id INT NOT NULL,
            book_id INT NOT NULL,
            quantity INT NOT NULL DEFAULT 1, 
            date_placed DATE NOT NULL,
            total_amount DECIMAL(10,2) NOT NULL,
            status VARCHAR(50) DEFAULT 'Placed',
            payment_method VARCHAR(100),
            PRIMARY KEY (order_id),
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (book_id) REFERENCES books(book_id)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS transactions (
            transaction_id VARCHAR(255) NOT NULL,
            user_id INT NOT NULL,
            order_id INT NOT NULL,
            total_amount DECIMAL(10, 2),
            PRIMARY KEY (transaction_id),
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE
        );

        """
    ]

    # Execute each table creation query
    for table in tables:
        cursor.execute(table)
    
    # Commit the changes
    conn.commit()

    print("Tables created successfully.")

    # Close cursor (optional as connection will be closed)
    cursor.close()



def add_author_to_db(conn, author_name, biography, birth_date, nationality):
    cursor = conn.cursor()
    query = """
        INSERT INTO authors (author_name, biography, birth_date, nationality)
        VALUES (%s, %s, %s, %s)
    """
    values = (author_name, biography, birth_date, nationality)
    cursor.execute(query, values)
    conn.commit()
    cursor.close()

def add_genre_to_db(conn, genre_name, description):
    cursor = conn.cursor()
    query = """
        INSERT INTO genre (genre_name, description)
        VALUES (%s, %s)
    """
    values = (genre_name, description)
    cursor.execute(query, values)
    conn.commit()
    cursor.close()

def add_book_to_db(conn, title, author_id, isbn, publisher_id, publication_year, genre_id, summary, language, price, stock, cover_image):
    cursor = conn.cursor()
    query = """
        INSERT INTO books (title, author_id, isbn, publisher_id, publication_year, genre_id, summary, language, price, stock, cover_image)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    values = (title, author_id, isbn, publisher_id, publication_year, genre_id, summary, language, price, stock, cover_image)
    cursor.execute(query, values)
    conn.commit()
    cursor.close()

def add_publisher_to_db(conn, publisher_name, headquarters, founding_year, website):
    cursor = conn.cursor()
    query = """
        INSERT INTO publishers (publisher_name, headquarters, founding_year, website)
        VALUES (%s, %s, %s, %s)
    """
    values = (publisher_name, headquarters, founding_year, website)
    cursor.execute(query, values)
    conn.commit()
    cursor.close()

def add_book_to_db(conn, title, author_id, isbn, publisher_id, publication_year, genre_id, summary, language, price, stock, cover_image):
    cursor = conn.cursor()
    query = """
        INSERT INTO books (title, author_id, isbn, publisher_id, publication_year, genre_id, summary, language, price, stock, cover_image)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    values = (title, author_id, isbn, publisher_id, publication_year, genre_id, summary, language, price, stock, cover_image)
    cursor.execute(query, values)
    conn.commit()
    cursor.close()


def add_review_to_db(conn, content, user_id, book_id, polarity, review_date):
    cursor = conn.cursor()
    query = """
        INSERT INTO reviews (content, user_id, book_id, polarity, review_date)
        VALUES (%s, %s, %s, %s, %s)
    """
    values = (content, user_id, book_id, polarity, review_date)
    cursor.execute(query, values)
    conn.commit()
    cursor.close()


def update_book_in_db(conn, book_id, title, author_id, isbn, publisher_id, publication_year,
                      genre_id, summary, language, price, stock, cover_image_path):
    cursor = conn.cursor()

        # Update the book record in the database
    cursor.execute("""
            UPDATE books
            SET title = %s,
                author_id = %s,
                isbn = %s,
                publisher_id = %s,
                publication_year = %s,
                genre_id = %s,
                summary = %s,
                language = %s,
                price = %s,
                stock = %s,
                cover_image = %s
            WHERE book_id = %s
        """, (title, author_id, isbn, publisher_id, publication_year, genre_id,
              summary, language, price, stock, cover_image_path, book_id))
        
    conn.commit()
    cursor.close()



# Initialize the database connection and create tables
conn = create_db_connection()
if conn:
    create_tables(conn)
    # Example usage: add an author
    # add_author_to_db(conn, "John Doe", "John Doe is a famous author known for his works in fiction.", "1980-01-01", "American")
    # Add more data as needed for authors, genres, publishers, and books
    conn.close()
