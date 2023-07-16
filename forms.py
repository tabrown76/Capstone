from flask_wtf import FlaskForm
from wtforms import StringField, EmailField, PasswordField, TextAreaField, SelectMultipleField
from wtforms.validators import ValidationError, DataRequired, Email, Length, EqualTo
from wtforms.widgets import CheckboxInput, ListWidget
from models import User, Character
from flask_login import current_user
import re

class UniqueUser(object):

    def __init__(self, message="User already exists."):
        self.message = message

    def __call__(self, form, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError(self.message)
        
class ComplexPassword(object):

        def __init__(self, message="Password must include at least one uppercase letter, one lowercase letter, one number, and one special character."):
            self.message = message

        def __call__(self, form, field):
            password = field.data

            if (re.search('[A-Z]', password) is None or
               re.search('[a-z]', password) is None or
               re.search('[0-9]', password) is None or
               re.search('[^A-Za-z0-9]', password) is None):
                 raise ValidationError(self.message)

class AddUserForm(FlaskForm):

    username = StringField('Username', validators=[DataRequired(), 
                                                   Length(min=4, max=25), 
                                                   UniqueUser()])
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    email = EmailField('E-mail', validators=[DataRequired(), 
                                             Email()])
    password = PasswordField('Password', validators=[DataRequired(), 
                                                     Length(min=8, message="Password must be at least 8 characters."),
                                                     EqualTo('confirm', message="Passwords must match."),
                                                     ComplexPassword()])
    confirm = PasswordField('Confirm Password', validators=[DataRequired()])
    image_url = StringField('(Optional) Image URL')

class LoginForm(FlaskForm):
    
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired(), 
                                                     Length(min=8)])

class EditUserForm(FlaskForm):
    
    username = StringField('Username', validators=[DataRequired()])
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    email = EmailField('E-mail', validators=[DataRequired(), 
                                             Email()])
    image_url = StringField('(Optional) Profile Image URL')
    password = PasswordField('Password', validators=[DataRequired(),
                                                     Length(min=8)])
    
class UniquePerUser(object):

    def __init__(self, user, message=None):
        self.user = user
        if not message:
            message = u'Character already exists.'
        self.message = message

    def __call__(self, form, field):
        existing_character = Character.query.filter_by(name=field.data, user_id=self.user.id).first()
        if existing_character:
            raise ValidationError(self.message)

class CharacterForm(FlaskForm):

    name = StringField('Character Name', validators=[DataRequired(),
                                                     Length(min=2, max=25),
                                                     UniquePerUser(lambda: current_user)])
    description = TextAreaField('Description', validators=[DataRequired(),
                                                           Length(max=250)])
    image_url = StringField('(Optional) Character Image URL')

class GenreForm(FlaskForm):

    genres = SelectMultipleField('Genres',
                                 choices = [],
                                 widget=ListWidget(prefix_label=False),
                                 option_widget=CheckboxInput(),
                                 coerce=int)