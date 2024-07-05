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
                cursor.execute("""
                    INSERT INTO orders (user_id, book_id, quantity, date_placed, total_amount, status, payment_method)
                    VALUES (%s, %s, %s, CURDATE(), %s, 'Placed', %s)
                """, (current_user.user_id, book_id, quantity, total_amount, payment_method))
                
                order_id = cursor.lastrowid
                cursor.execute("DELETE FROM carts WHERE user_id = %s AND book_id = %s", (current_user.user_id, book_id))
                
                conn.commit()
                print(f"Order placed for Order ID: {order_id}")
                conn.close()

                return redirect(url_for('order_summary', order_id=order_id))

            except Exception as e:
                conn.rollback()
                flash(f"Transaction failed: {str(e)}", 'danger')
                print(f"Transaction failed: {str(e)}")
                conn.close()
        else:
            flash("Invalid payment method selected", 'danger')
            conn.close()
            return redirect(url_for('place_order', book_id=book_id))  # Redirect back to place_order page if payment method is invalid
    
    return render_template('place_order.html', book=book, user=current_user)
@app.route('/book/<int:book_id>/reviews')
@login_required
def book_reviews(book_id):
    conn = create_db_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)

        # Query to fetch book details
        book_query = """
            SELECT b.title, a.author_name, g.genre_name, p.publisher_name, b.price,
                   b.publication_year, b.isbn, b.summary, b.language, b.stock, b.cover_image,
                   AVG(r.rating) AS avg_rating
            FROM books b
            INNER JOIN authors a ON b.author_id = a.author_id
            INNER JOIN genre g ON b.genre_id = g.genre_id
            INNER JOIN publishers p ON b.publisher_id = p.publisher_id
            LEFT JOIN reviews r ON b.book_id = r.book_id
            WHERE b.book_id = %s
            GROUP BY b.book_id
        """
        
        # Query to fetch reviews for the book
        reviews_query = """
            SELECT r.content, r.rating, u.username, r.review_date
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
                return render_template('book_reviews.html', book=book, reviews=reviews)
            else:
                flash('Book not found!', 'danger')
                conn.close()
                return redirect(url_for('home'))

        except Exception as e:
            flash(f"Error fetching book details: {str(e)}", 'danger')
            conn.close()
            return redirect(url_for('home'))

    else:
        flash("Failed to connect to the database.", 'danger')
        return redirect(url_for('home'))


# ADD REVIEWS 
@app.route('/add_review/<int:book_id>', methods=['POST'])
def add_review(book_id):
    form = ReviewForm()

    if form.validate_on_submit():
        # Extract review content from form
        review_content = form.content.data.strip()
        
        # Check if user is logged in (example: using session)
        if 'user_id' not in session:
            flash('You must be logged in to add a review.', 'danger')
            return redirect(url_for('login'))  # Adjust login route as per your application

        # Analyze sentiment polarity
        polarity_category = analyze_sentiment(review_content)

        # Insert the review into the database
        conn = create_db_connection()  # Assume create_db_connection() is defined elsewhere
        if conn:
            try:
                cursor = conn.cursor()
                query = """
                    INSERT INTO reviews (content, user_id, book_id, polarity, review_date)
                    VALUES (%s, %s, %s, %s, %s)
                """
                # Example: Replace user_id with actual logged in user ID
                user_id = session['user_id']  # Fetch user ID from session

                # Execute the query
                cursor.execute(query, (review_content, user_id, book_id, polarity_category, date.today()))
                conn.commit()
                conn.close()

                flash('Review added successfully!', 'success')
                return redirect(url_for('book_details', book_id=book_id))

            except Exception as e:
                conn.rollback()
                conn.close()
                flash(f'Error adding review: {str(e)}', 'danger')

    # If form validation fails or any other error occurs, redirect back to book details
    return redirect(url_for('book_details', book_id=book_id))


@app.route('/cart', methods=['GET'])
@login_required
def cart():
    try:
        conn = create_db_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)
            
            # Fetch cart items for the current user with book details
            cursor.execute("""
                SELECT c.cart_id, b.title, b.price, c.quantity, c.cart_date, b.cover_image
                FROM carts c
                JOIN books b ON c.book_id = b.book_id
                WHERE c.user_id = %s
            """, (current_user.user_id,))
            
            cart_items = cursor.fetchall()
            conn.close()
            
            return render_template('cart.html', cart_items=cart_items)
        
        else:
            flash('Failed to connect to the database.', 'danger')
            return redirect(url_for('home'))
    
    except mysql.connector.Error as e:
        flash(f"Database error", 'danger')
        return redirect(url_for('home'))



# DELETE ITEMS FROM CART
@app.route('/delete_from_cart/<int:cart_id>', methods=['POST'])
@login_required
def delete_from_cart(cart_id):
    conn = create_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM carts WHERE cart_id = %s AND user_id = %s", (cart_id, current_user.user_id))
        conn.commit()
        flash('Item deleted from cart successfully!', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Error deleting item from cart', 'danger')
    finally:
        conn.close()

    return redirect(url_for('cart'))
