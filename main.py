from flask import Flask, render_template, redirect, url_for, flash, request, abort, jsonify
import stripe
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user
from forms import CreateArticleForm, RegisterForm, LoginForm, CommentForm, EmailForm
from bleach import clean
from flask_mail import Mail, Message
from flask_gravatar import Gravatar
from functools import wraps
import os
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'sqlite:///product.db')
ckeditor = CKEditor(app)
Bootstrap(app)

gravatar = Gravatar(app, size=100, rating='g', default='retro', force_default=False,
                    force_lower=False, use_ssl=False, base_url=None)

# CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///product.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)

# Set your Stripe publishable key in the Flask app configuration
app.config[
    'STRIPE_PUBLISHABLE_KEY'] = \
    'pk_test_51NtGrNCE7CUcTtCePGZ8PU6PpV1dth3S3i0QFcOTuk1aP1jceAUg3MdLmYyMJfnT8o7gO2Cv6bGKofqlET8p5VLi00woinclWL'

# CONNECT TO Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'  # Use Gmail SMTP server
app.config['MAIL_PORT'] = 587  # Port for TLS
app.config['MAIL_USE_TLS'] = True  # Use TLS for security
app.config['MAIL_USE_SSL'] = False  # Do not use SSL
app.config['MAIL_USERNAME'] = os.getenv('EMAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('EMAIL_PASSWORD')

mail = Mail(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


# CREATE THE USER TABLE IN DB
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    is_admin = db.Column(db.Boolean, default=False)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(100))

    # This will act like a List of BlogPost objects attached to each User.
    # The "author" refers to the author property in the BlogPost class.
    products = relationship("ProductArticle", back_populates="author")

    # ******* Add parent relationship ******* #
    # "comment_author" refers to the comment_author property in the Comment class.
    comments = relationship("Comment", back_populates="comment_author")


# CONFIGURE THE BLOG POST TABLES
class ProductArticle(db.Model):
    __tablename__ = "product_articles"
    id = db.Column(db.Integer, primary_key=True)

    # Create Foreign Key, "users.id" the users refers to the tablename of User.
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    # Create reference to the User object, the "posts" refers to the posts property in the User class.
    author = relationship("User", back_populates="products")

    title = db.Column(db.String(250), unique=True, nullable=False)
    price = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)

    # *************** Parent Relationship ************* #
    comments = relationship("Comment", back_populates="parent_article")


class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)

    # ******* Add child relationship ******* #
    # "users.id" The users refer to the tablename of the Users class.
    # "comments" refers to the comments property in the User class.
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    comment_author = relationship("User", back_populates="comments")

    # *************** Child Relationship ************* #
    article_id = db.Column(db.Integer, db.ForeignKey("product_articles.id"))
    parent_article = relationship("ProductArticle", back_populates="comments")

    text = db.Column(db.Text, nullable=False)


with app.app_context():
    db.create_all()


@app.route('/')
def get_all_articles():
    articles = ProductArticle.query.all()
    return render_template("get-all-articles.html", all_articles=articles, current_user=current_user,
                           stripe_publishable_key=app.config['STRIPE_PUBLISHABLE_KEY'],
                           date=datetime.now().strftime("%a %d %B %Y"))


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():

        # If user's email already exists
        if User.query.filter_by(email=form.email.data).first():
            print(User.query.filter_by(email=form.email.data).first())
            # Send a flash message
            flash("You've already signed up with that email, log in instead!")
            return redirect(url_for('login'))

        hash_and_salted_password = generate_password_hash(
            request.form.get('password'),
            method='pbkdf2:sha256',
            salt_length=8
        )

        new_user = User()
        new_user.email = request.form['email']
        new_user.name = request.form['name']
        new_user.password = hash_and_salted_password
        # new_user.is_admin = True  # Set this user as an admin

        db.session.add(new_user)
        db.session.commit()

        # Log in and authenticate the user after adding details to the database.
        login_user(new_user)

        print(f'New username: {new_user.name}\n email: {new_user.email}\n password: {new_user.password}')

        return redirect(url_for('get_all_articles'))

    return render_template("register.html", form=form, current_user=current_user,
                           date=datetime.now().strftime("%a %d %B %Y"))


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = request.form.get('email')
        password = request.form.get('password')

        # Find user by email entered.
        user = User.query.filter_by(email=email).first()

        # Email doesn't exist
        if not user:
            flash("That email does not exist, please try again.")
            return redirect(url_for('login'))
        # Password incorrect
        elif not check_password_hash(user.password, password):
            flash('Password incorrect, please try again.')
            return redirect(url_for('login'))
        # Email exists and password correct
        else:
            login_user(user)
            return redirect(url_for('get_all_articles'))

    return render_template("login.html", form=form, current_user=current_user,
                           date=datetime.now().strftime("%a %d %B %Y"))


@app.route('/logout')
def logout():
    logout_user()
    print(f"Is user authenticated after logout? {current_user.is_authenticated}")
    return redirect(url_for('get_all_articles'))


@app.route("/article/<int:article_id>", methods=["GET", "POST"])
def show_article(article_id):
    form = CommentForm()
    requested_article = ProductArticle.query.get(article_id)

    if form.validate_on_submit():
        if not current_user.is_authenticated:
            flash("You need to login or register to comment.")
            return redirect(url_for("login"))

        new_comment = Comment(
            text=form.comment_text.data,
            comment_author=current_user,
            parent_article=requested_article
        )
        db.session.add(new_comment)
        db.session.commit()

    return render_template("article.html", article=requested_article, form=form, current_user=current_user,
                           date=datetime.now().strftime("%a %d %B %Y"))


@app.route("/about")
def about():
    return render_template("about.html", current_user=current_user,
                           date=datetime.now().strftime("%a %d %B %Y"))


@app.route("/contact", methods=['GET', 'POST'])
def contact():
    form = EmailForm()
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        email_message = request.form['email_message']

        # Sanitize the email_message to remove unwanted HTML tags
        email_message = clean(email_message, tags=[], attributes={}, strip=True)

        # Name incorrect
        if not name:
            flash("Please Enter A Nam€ ¡!¡", 'danger')
            return redirect(url_for('contact'))
        # Email incorrect
        elif '@' not in email:
            flash('Please Enter Your €mail ¡!¡', 'danger')
            return redirect(url_for('contact'))
        # Phone incorrect

        if not str(phone).isdigit():
            flash('Please Enter Your Phone Numb€r ¡!¡', 'danger')
            return redirect(url_for('contact'))
        # Message incorrect
        elif not email_message:
            flash('Please Enter Your Messag€ ¡!¡', 'danger')
            return redirect(url_for('contact'))

        # Create an email message
        msg = Message('Contact Form Submission', sender=email, recipients=['medusadbt@gmail.com'])
        msg.body = f'Name: {name}\nEmail: {email}\nPhone: {phone}\nMessage: {email_message}'

        try:
            # Send the email
            mail.send(msg)
            flash('Your message has been sent successfully ¡!¡', 'success')
        except Exception as e:
            flash('An error occurred while sending your message. Please try again later.', 'danger')
            print(str(e))

        return redirect(url_for('contact'))

    return render_template("contact.html", current_user=current_user, form=form,
                           date=datetime.now().strftime("%a %d %B %Y"))


# Create admin-only decorator
def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # If the user is not an admin, return a 403 error
        if not current_user.is_admin:
            return abort(403)
        return f(*args, **kwargs)

    return decorated_function


@app.route("/new-article", methods=['GET', 'POST'])
# Mark with decorator
@admin_only
def add_new_article():
    form = CreateArticleForm()
    if form.validate_on_submit():
        new_article = ProductArticle(
            title=form.title.data,
            price=form.price.data,
            body=form.body.data,
            img_url=form.img_url.data,
            author=current_user,
            date=date.today().strftime("%B %d, %Y")
        )
        db.session.add(new_article)
        db.session.commit()

        # Get the ID of the newly created article
        new_article_id = new_article.id

        # Redirect to the show_article route for the new article
        return redirect(url_for("show_article", article_id=new_article_id))

    return render_template("make-article.html", form=form, current_user=current_user,
                           date=datetime.now().strftime("%a %d %B %Y"))


@app.route("/edit-article/<int:article_id>", methods=['GET', 'POST'])
# Mark with decorator
@admin_only
def edit_article(article_id):
    article = ProductArticle.query.get(article_id)
    edit_form = CreateArticleForm(
        title=article.title,
        price=article.price,
        img_url=article.img_url,
        author=current_user,
        body=article.body
    )
    if edit_form.validate_on_submit():
        article.title = edit_form.title.data
        article.price = edit_form.price.data
        article.img_url = edit_form.img_url.data
        article.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for("show_article", article_id=article.id))

    return render_template("make-article.html", form=edit_form, is_edit_article=True,
                           current_user=current_user, date=datetime.now().strftime("%a %d %B %Y"))


@app.route("/delete/<int:article_id>")
# Mark with decorator
@admin_only
def delete_article(article_id):
    article_to_delete = ProductArticle.query.get(article_id)
    db.session.delete(article_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_articles'))


@app.route("/delete-comment/<int:comment_id>")
# Mark with decorator
@admin_only
def comment_to_delete(comment_id):
    delete_comment = Comment.query.get(comment_id)
    db.session.delete(delete_comment)
    db.session.commit()
    return redirect(url_for('get_all_articles'))


## Initialize Stripe with your secret key
#stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
#
#
#@app.route('/payment/<int:article_id>', methods=['GET', 'POST'])
#def payment(article_id):
#    article = ProductArticle.query.get(article_id)
#    charge = None  # Initialize charge to None
#
#    if request.method == 'POST':
#        # Get the token generated by the Stripe.js on the client-side
#        token = request.form['stripeToken']
#        try:
#            # Create a charge using the token and charge amount
#            charge = stripe.Charge.create(
#                amount=int(float(article.price) * 100),  # Convert price to cents
#                currency='usd',
#                source=token,
#                description=f'Payment for {article.title}'
#            )
#            print(f'payment charge: {charge}')
#            # Payment successful, you can update your database or perform other actions here
#            flash('Payment successful!', 'success')
#        except stripe.error.CardError as e:
#            # Card was declined
#            flash(f'Payment failed: {e.error.message}', 'danger')
#
#    return render_template("payment.html", article=article, charge=charge)
#
#
## Define the /pay/<int:article_id> route to handle payments
#@app.route('/pay/<int:article_id>', methods=['GET', 'POST'])
#def pay(article_id):
#    # Retrieve the article based on the provided article_id
#    article = ProductArticle.query.get(article_id)
#
#    # Get the token generated by the Stripe.js on the client-side
#    token = request.form['stripeToken']
#
#    try:
#        # Extract the numeric part of the price and convert it to cents
#        price_in_euros = article.price  # e.g., "€ 9.19"
#        price_numeric = float(''.join(filter(str.isdigit, price_in_euros)))  # Extracts 919
#        price_in_cents = int(price_numeric * 100)  # Convert to cents (e.g., 919)
#
#        # Create a charge using the token and converted price
#        charge = stripe.Charge.create(
#            amount=price_in_cents,
#            currency='usd',
#            source=token,
#            description=f'Payment for {article.title}'
#        )
#        print(f'charge: {charge}')
#        # Payment successful, you can update your database or perform other actions here
#        return jsonify({'success': True})  # Return a JSON response indicating success
#    except stripe.error.CardError as e:
#        # Card was declined
#        return jsonify({'success': False, 'error': e.error.message})  # Return a JSON response with error message


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
