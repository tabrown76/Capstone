from flask_wtf import FlaskForm
from wtforms import StringField, EmailField, PasswordField, TextAreaField, SelectMultipleField
from wtforms.validators import ValidationError, DataRequired, Email, Length, EqualTo
from wtforms.widgets import CheckboxInput, ListWidget
from models import User, Character
from flask_login import current_user
import re

class UniqueUser(object):
    """
    Validator to check if a username already exists.

    This validator queries the User model to check if a username already exists in the database. If a user with the same username is found, it raises a ValidationError with a custom message.

    Attributes:
        message (str): The validation error message to display when a user with the same username is found.

    """

    def __init__(self, message="User already exists."):
        self.message = message

    def __call__(self, form, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError(self.message)
        
class UniqueEmail(object):
    """
    Validator for ensuring the uniqueness of an email.

    This validator queries the User model to verify if the provided email already exists in the database. If a match is found, it raises a ValidationError with a custom message.

    Args:
        message (str, optional): Custom error message to display when an email is already in use. Defaults to "E-mail already taken."

    Methods:
        __call__(self, form, field): Method that performs the actual validation. Called when the validator is applied to a form field.

    Raises:
        ValidationError: If an email address is already associated with an existing user in the database.
    """

    def __init__(self, message="E-mail already taken."):
        self.message = message

    def __call__(self, form, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError(self.message)
        
class ComplexPassword(object):
    """
    Validator for ensuring the complexity of a password.

    This validator uses regular expressions to verify that the provided password meets the specified complexity criteria:
    at least one uppercase letter, one lowercase letter, one number, and one special character.

    Args:
        message (str, optional): Custom error message to display when a password does not meet the complexity criteria. 
        Defaults to "Password must include at least one uppercase letter, one lowercase letter, one number, and one special character."

    Methods:
        __call__(self, form, field): Method that performs the actual validation. Called when the validator is applied to a form field.

    Raises:
        ValidationError: If a password does not meet the required complexity criteria.
    """

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
    """
    Form for adding a new user.

    This form contains fields for the username, first name, last name, email, password, confirmation of the password,
    and an optional image URL. Validators are used to ensure that all fields meet the specified requirements.

    Fields:
        username (StringField): Field for the username. The username is required, has to be unique, and its length must be between 4 and 25 characters.
        first_name (StringField): Field for the user's first name. This field is required.
        last_name (StringField): Field for the user's last name. This field is required.
        email (EmailField): Field for the user's email. The email is required, must be valid, and has to be unique.
        password (PasswordField): Field for the user's password. The password is required, must be at least 8 characters long, and must match the confirmation password.
        confirm (PasswordField): Field for the confirmation of the user's password. This field is required.
        image_url (StringField): Optional field for an image URL associated with the user.
    """

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
    """
    Form for user login.

    This form contains fields for the username and password. Validators are used to ensure 
    that both fields meet the specified requirements.

    Fields:
        username (StringField): Field for the username. This field is required.
        password (PasswordField): Field for the password. This field is required and its length must be at least 8 characters.
    """
    
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired(), 
                                                     Length(min=8)])

class EditUserForm(FlaskForm):
    """
    Form for editing user details.

    This form is used when a user wants to edit their personal information. 
    It includes fields for first name, last name, email, optional profile image URL, and password. 
    Validators are used to ensure that required fields meet the specified requirements.

    Fields:
        first_name (StringField): Field for the first name. This field is required.
        last_name (StringField): Field for the last name. This field is required.
        email (EmailField): Field for the email address. This field is required and must contain a valid email format.
        image_url (StringField): Optional field for a profile image URL.
        password (PasswordField): Field for the password. This field is required and its length must be at least 8 characters.
    """
    
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    email = EmailField('E-mail', validators=[DataRequired(), 
                                             Email()])
    image_url = StringField('(Optional) Profile Image URL')
    password = PasswordField('Password', validators=[DataRequired(),
                                                     Length(min=8)])
    
class UniquePerUser(object):
    """
    Custom validator to ensure character uniqueness per user.

    This class is used to create a validator that checks if a character name 
    already exists for the authenticated user. If a character with the same name exists, 
    a validation error is raised.

    Args:
        message (str, optional): The error message to display when validation fails. 
                                 Defaults to 'Character already exists.' if not provided.

    Methods:
        __call__(self, form, field): Method to perform the validation. Called when the form is validated.
    """

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
    """
    FlaskForm subclass to handle character data input and validation.

    This form is used to input data for a new character or to edit an existing one. 
    It includes fields for the character's name, description, and an optional image URL.

    Attributes:
        name (wtforms.StringField): Field to input the character's name. It requires data and has length limitations.
                                     It also uses the `UniquePerUser` custom validator to ensure unique character names per user.
        description (wtforms.TextAreaField): Field to input the character's description. Requires data and has a length limit.
        image_url (wtforms.StringField): Optional field to input a URL for a character image.

    Note:
        This form does not handle the submission of data to the database itself, 
        but rather it structures and validates the data.
    """

    name = StringField('Character Name', validators=[DataRequired(),
                                                     Length(min=2, max=25),
                                                     UniquePerUser()])
    description = TextAreaField('Description', validators=[DataRequired(),
                                                           Length(max=250)])
    img_url = StringField('(Optional) Character Image URL')

class GenreLimit(object):
    """
    Custom validator to limit the number of genre selections in a form.

    This validator checks if the selected genres in the form exceed a set limit. 
    If the limit is exceeded, it raises a ValidationError with a specified message.

    Attributes:
        message (str): The message to display when validation fails due to too many genres being selected. 
                       Defaults to 'Please select up to 3 genres.'

    Methods:
        __call__(form, field): Implements the actual validation logic. If the number of selected genres 
                               in the provided field exceeds 3, it raises a ValidationError.
        
    Usage:
        To use this validator, include it in the list of validators in the relevant field in the form:
        genres = SelectMultipleField('Genres (Select up to 3)', validators=[GenreLimit()])
    """

    def __init__(self, message=None):
        if not message:
            message = 'Please select up to 3 genres.'
        self.message = message

    def __call__(self, form, field):
        if len(field.data) > 3:
            raise ValidationError(self.message)

class GenreForm(FlaskForm):
    """
    Form for handling the selection of genres in the application.

    This form provides a multiple selection field for genres. It uses a custom widget
    to display checkboxes for each genre option. It also employs a custom validator
    (`GenreLimit`) to limit the number of genres that a user can select.

    Attributes:
        genres (SelectMultipleField): A field for users to select one or more genres. 
                                      The field uses custom widgets and validators.
                                      The field's choices attribute is set at runtime.
                                      The field's data is coerced to int.

    Usage:
        To use this form in a view, instantiate it and pass it to the template:
        form = GenreForm()
        render_template('template.html', form=form)

        In the template, you can loop over `form.genres` to display each checkbox option:
        {% for subfield in form.genres %}
            {{ subfield }}
        {% endfor %}
    """

    genres = SelectMultipleField('Genres (Select up to 3)',
                                 choices = [],
                                 widget=ListWidget(prefix_label=False),
                                 option_widget=CheckboxInput(),
                                 coerce=int,
                                 validators=[GenreLimit()])

class EditStoryForm(FlaskForm):
    """
    Form for handling the editing of a story in the application.

    This form provides fields for the story title and an optional cover image URL.
    It uses validators to ensure that the title field is not empty and does not 
    exceed a certain length.

    Attributes:
        title (StringField): A field for the story's title, required, 
                             with a length limit between 2 to 50 characters.
        img_url (StringField): An optional field for the story's cover image URL.

    Usage:
        To use this form in a view, first fetch the story you want to edit, then 
        populate the form with the story's current data, and pass it to the template:
        
        form = EditStoryForm(obj=story)
        render_template('edit_story.html', form=form)

        In the template, you can use `form.title` and `form.img_url` to display each 
        field and let the user edit them.
    """

    title = StringField('Title', validators=[DataRequired(),
                                             Length(min=2, max=50)])
    img_url = StringField('(Optional) Cover Image URL')