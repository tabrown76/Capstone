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
        
class UniqueEmail(object):

    def __init__(self, message="E-mail already taken."):
        self.message = message

    def __call__(self, form, field):
        if User.query.filter_by(email=field.data).first():
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
                                             Email(),
                                             UniqueEmail()])
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
    
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    email = EmailField('E-mail', validators=[DataRequired(), 
                                             Email()])
    image_url = StringField('(Optional) Profile Image URL')
    password = PasswordField('Password', validators=[DataRequired(),
                                                     Length(min=8)])
    
class UniquePerUser(object):

    def __init__(self, message=None):
        if not message:
            message = 'Character already exists.'
        self.message = message

    def __call__(self, form, field):
        if current_user.is_authenticated:
            existing_character = Character.query.filter(Character.name.ilike(field.data), Character.user_id==current_user.id).first()
            if existing_character and existing_character.name != field.data:
                raise ValidationError(self.message)

class CharacterForm(FlaskForm):

    name = StringField('Character Name', validators=[DataRequired(),
                                                     Length(min=2, max=25),
                                                     UniquePerUser()])
    description = TextAreaField('Description', validators=[DataRequired(),
                                                           Length(max=250)])
    image_url = StringField('(Optional) Character Image URL')

class GenreLimit(object):

    def __init__(self, message=None):
        if not message:
            message = 'Please select up to 3 genres.'
        self.message = message

    def __call__(self, form, field):
        if len(field.data) > 3:
            raise ValidationError(self.message)

class GenreForm(FlaskForm):

    genres = SelectMultipleField('Genres (Select up to 3)',
                                 choices = [],
                                 widget=ListWidget(prefix_label=False),
                                 option_widget=CheckboxInput(),
                                 coerce=int,
                                 validators=[GenreLimit()])

class EditStoryForm(FlaskForm):

    title = StringField('Title', validators=[DataRequired(),
                                             Length(min=2, max=50)])
    img_url = StringField('(Optional) Cover Image URL')