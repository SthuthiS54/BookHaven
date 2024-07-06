
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, IntegerField, TextAreaField, DecimalField, DateField, SelectField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, URL, NumberRange
from flask_wtf.file import FileField, FileAllowed
from werkzeug.utils import secure_filename

class RegistrationForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=255)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=255)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=255)])
    age = IntegerField('Age')
    contact = StringField('Contact')
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=50)])
    address = StringField('Address', validators=[Length(max=255)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6, max=255)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=255)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6, max=255)])
    submit = SubmitField('Log In')


class BookForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=255)])
    author_id = SelectField('Author', coerce=int, validators=[DataRequired()])
    isbn = StringField('ISBN', validators=[Length(max=20)])
    publisher_id = SelectField('Publisher', coerce=int, validators=[DataRequired()])
    publication_year = IntegerField('Publication Year')
    genre_id = SelectField('Genre', coerce=int, validators=[DataRequired()])
    summary = TextAreaField('Summary')
    language = StringField('Language', validators=[Length(max=50)])
    price = DecimalField('Price', places=2)
    stock = IntegerField('Stock')
    cover_image = FileField('Cover Image', validators=[DataRequired()])


class EditBookForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    author_id = SelectField('Author', coerce=int, validators=[DataRequired()])
    isbn = StringField('ISBN', validators=[Length(max=20)])
    publisher_id = SelectField('Publisher', coerce=int, validators=[DataRequired()])
    publication_year = IntegerField('Publication Year', validators=[DataRequired()])
    genre_id = SelectField('Genre', coerce=int, validators=[DataRequired()])
    summary = TextAreaField('Summary', validators=[DataRequired()])
    language = StringField('Language', validators=[Length(max=50)])
    price = DecimalField('Price', places=2, validators=[DataRequired()])
    stock = IntegerField('Stock', validators=[DataRequired()])
    cover_image = FileField('Cover Image')





class AuthorForm(FlaskForm):
    author_name = StringField('Author Name', validators=[DataRequired()])
    biography = TextAreaField('Biography')
    birth_date = DateField('Birth Date (YYYY-MM-DD)')
    nationality = StringField('Nationality')
    submit = SubmitField('Add Author')

class GenreForm(FlaskForm):
    genre_name = StringField('Genre Name', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    submit = SubmitField('Add Genre')

class PublisherForm(FlaskForm):
    publisher_name = StringField('Publisher Name', validators=[DataRequired()])
    headquarters = StringField('Headquarters', validators=[DataRequired()])
    founding_year = IntegerField('Founding Year', validators=[DataRequired()])
    website = StringField('Website', validators=[DataRequired()])
    submit = SubmitField('Add Publisher')

class OrderForm(FlaskForm):
    quantity = IntegerField('Quantity', validators=[DataRequired(), NumberRange(min=1, message="Quantity must be at least 1")])
    address = StringField('Address', validators=[DataRequired()])
    payment_method = SelectField('Payment Method', choices=[('cash', 'Cash on Delivery'), ('online', 'Online Payment')], validators=[DataRequired()])
    submit = SubmitField('Place Order')

class ReviewForm(FlaskForm):
    content = TextAreaField('Review', validators=[DataRequired()])
    submit = SubmitField('Add Review')

class StarRatingForm(FlaskForm):
    rating = IntegerField('Rating', validators=[DataRequired()])
    submit = SubmitField('Submit')