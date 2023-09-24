from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, IntegerField, validators
from wtforms.validators import DataRequired, URL, Email
from flask_ckeditor import CKEditorField


# WTForm
class CreateArticleForm(FlaskForm):
    title = StringField("Article Title", validators=[DataRequired()])
    price = StringField("Price (£)", validators=[DataRequired()])
    img_url = StringField("Product Image URL", validators=[DataRequired(), URL()])
    body = CKEditorField("Product Content", validators=[DataRequired()])
    author = StringField("Product Author")
    author_id = StringField("Author_id")
    submit = SubmitField("SUBMIT PRODUCT ¡!¡")


class RegisterForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(Email), validators.Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    name = StringField("Name", validators=[DataRequired()])
    submit = SubmitField("SIGN M€ UP ¡!¡")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(Email), validators.Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("LET M€ IN ¡!¡")


class EmailForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(Email), validators.Email()])
    phone = IntegerField("Phone Number", validators=[DataRequired()])
    email_message = CKEditorField("Message", validators=[validators.DataRequired()])
    submit = SubmitField("S€ND ¡!¡")


class CommentForm(FlaskForm):
    comment_text = CKEditorField("Comment", validators=[DataRequired()])
    submit = SubmitField('SUBMIT COMMENT ¡!¡')
