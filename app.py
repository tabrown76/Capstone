from flask import Flask, render_template, redirect, url_for, request, flash, session
from flask_login import LoginManager, login_required, current_user, logout_user, login_user
from models import db, connect_db, User, Story, StoryStep, Choice, Genre, Character, UserGenre
from forms import AddUserForm, LoginForm, EditUserForm, GenreForm, CharacterForm, EditStoryForm
from flask_mail import Mail, Message
from utils import email_confirmed_required, send_confirmation_email, confirm_token
from apicalls import make_api_request, next_step
from sqlalchemy import func
from werkzeug.exceptions import HTTPException
from datetime import datetime
from time import time
from flask_migrate import Migrate
import os
import openai

app = Flask (__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = (os.environ.get("DATABASE_URL", "postgresql:///ai_venture"))
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = True
app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY")

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv("MAIL_USERNAME")
app.config['MAIL_DEFAULT_SENDER'] = os.getenv("MAIL_USERNAME")
app.config['MAIL_PASSWORD'] = os.getenv("MAIL_PASSWORD")
app.config['SECURITY_PASSWORD_SALT'] = os.getenv("SECURITY_PASSWORD_SALT")

mail = Mail(app)

login_manager = LoginManager()
login_manager.init_app(app)

migrate = Migrate(app, db)

connect_db(app)

@app.errorhandler(Exception)
def handle_exception(e):
    """
    Handle general exceptions.

    This function handles all exceptions and returns the HTTPException if it is an instance of HTTPException.
    Otherwise, it redirects to the 'unhandled_exception' route. This is a part of the Flask error handling system.
    
    Args:
        e (Exception): The exception that was raised.

    Returns:
        HTTPException or Werkzeug Response: Returns the HTTPException if e is an instance of it. Otherwise, 
        it returns a redirection to 'unhandled_exception' route.
    """

    if isinstance(e, HTTPException):
        return e
    
    return redirect(url_for('unhandled_exception'))

@app.route('/oops')
def unhandled_exception():
    """
    Handle unhandled exceptions.

    This function is used to handle all exceptions that are not explicitly caught elsewhere in the application.
    It renders the 'oops.html' template, which is typically used to display an error message to the user.

    Returns:
        Rendered template (str): Returns the 'oops.html' template which is used for displaying the error message.
    """

    return render_template('oops.html')


@login_manager.user_loader
def load_user(user_id):
    """
    Load user from the database.

    This function is decorated with '@login_manager.user_loader' and it's used by Flask-Login to 
    load a user from the User model. It's essential for managing the user session. 

    Args:
        user_id (int): A user ID.

    Returns:
        User or None: It returns a User object if the user is found, or None if the user is not found.
    """

    return User.query.get(int(user_id))

@app.route('/', methods=["GET", "POST"])
def homepage():
    """
    Render the homepage.

    This function is responsible for handling requests to the root URL of the application.
    If the current user is authenticated, it fetches genres and characters associated with 
    the user and renders 'home.html' template. If the user is not authenticated, it renders 
    the 'home-anon.html' template.

    Returns:
        Rendered template (str): Returns the 'home.html' template if the user is authenticated,
        or the 'home-anon.html' template if the user is not authenticated.
    """

    if current_user.is_authenticated:

        form = GenreForm()
        genres = Genre.query.all()
        form.genres.choices = [(genre.id, genre.name) for genre in genres]
        page = request.args.get('page', 1, type=int)
        characters = Character.query.filter_by(user_id=current_user.id).paginate(page=page, per_page=20)          
        
        return render_template('home.html', id=current_user.id, form=form, characters=characters)
    else:
        return render_template('home-anon.html')

@app.route('/user/signup', methods=["GET", "POST"])
def signup():
    """
    Handle the user sign-up process.

    This function handles both GET and POST requests to the '/user/signup' route. 
    For a GET request, it provides the user with a sign-up form to enter their details.
    For a POST request, it takes the data provided by the user, validates it, and if valid, 
    creates a new user account, commits the changes to the database, logs the user in, sends a confirmation 
    email and then redirects the user to the 'thanks' page. If the data provided is not valid, it re-renders 
    the sign-up form with errors.

    Returns:
        Rendered template or redirect function: 
        For a GET request, or for a POST request where the data is not valid, 
        it returns the 'users/signup.html' template with the form.
        For a POST request where the data is valid, it redirects the user to the 'thanks' page.
    """

    form = AddUserForm()

    if request.method == "POST" and form.validate_on_submit():
        user_data = {field.name: getattr(form, field.name).data for field in form}
        new_user = User.signup(user_data)

        db.session.commit()
        login_user(new_user)
        send_confirmation_email(mail, app, new_user.email)       
        flash("Confirmation email sent.", "info")

        return redirect(url_for('thanks'))


    return render_template('/users/signup.html', form=form)

@app.route('/user/login', methods=["GET", "POST"])
def login():
    """
    Manage the user login process.

    This function handles both GET and POST requests to the '/user/login' route.
    For a GET request, it serves a form for the user to enter their login credentials.
    For a POST request, it validates the user's input against the data in the database. If the credentials are valid 
    and the user's email is confirmed, it logs the user in, displays a welcome message and redirects them to the homepage. 
    If the credentials are valid but the email is not confirmed, it logs the user in, instructs them to confirm their email,
    and redirects to the 'unconfirmed' route. If the credentials are not valid, it flashes an invalid credentials message.

    Returns:
        Rendered template or redirection: 
        For a GET request, or for a POST request with invalid credentials, it returns the 'users/login.html' 
        template with the form and any applicable errors.
        For a POST request with valid credentials, it redirects the user to the appropriate route based on the 
        confirmation status of the user's email.
    """

    form = LoginForm()

    if request.method == "POST" and form.validate_on_submit():
        user = User.authenticate(form.username.data,
                                 form.password.data)
        
        if user and user.email_confirmed:
            login_user(user)
            flash(f"Welcome back, {user.username}!", "success")
            return redirect(url_for('homepage'))
        
        elif user:
            login_user(user)
            flash('Please confirm e-mail.', 'danger')
            return redirect(url_for('unconfirmed'))
        
        else:
            flash("Invalid Username/Password combination.", "danger")

    return render_template('/users/login.html', form=form)

@app.route('/user/confirm', methods=["GET", "POST"])
@login_required
def unconfirmed():
    """
    Manage the process of user email confirmation.

    This function handles both GET and POST requests to the '/user/confirm' route. 
    It requires the user to be logged in, which is ensured by the '@login_required' decorator.

    For a GET request, it checks if the user's email is already confirmed. If confirmed, it informs the user
    and redirects them to the homepage. If not confirmed, it renders the 'unconfirmed.html' template which provides
    options to resend the confirmation email.

    For a POST request, it checks if a confirmation email was sent within the last 5 minutes. If not, it sends a 
    new confirmation email, flashes a confirmation message, and redirects the user to the 'thanks' page. If an email 
    was sent within the last 5 minutes, it informs the user to check their spam folder or wait before trying again.

    Returns:
        Rendered template or redirection: 
        For a GET request, it either redirects the user to the homepage or returns the 'unconfirmed.html' template.
        For a POST request, it either redirects the user to the 'thanks' page or returns the 'unconfirmed.html' template.
    """

    if current_user.email_confirmed:
        flash('Your email is already confirmed.', 'info')
        return redirect(url_for('homepage'))

    if request.method == "POST":
        key = 'unconfirmed_last_call'

        if key in session: 
            
            if time() < session[key] + 300:
                flash('Please check your spam folder, or wait 5 minutes to try again.', 'danger')
                return render_template('unconfirmed.html')
            
        send_confirmation_email(mail, app, current_user.email)
        flash("Confirmation email sent.", "info")
        session[key] = time()
        return redirect(url_for('thanks'))

    return render_template('unconfirmed.html')

@app.route('/user/confirm/<token>', methods=["GET", "POST"])
def confirm_email(token):
    """
    Validate the user's email confirmation token.

    This function handles both GET and POST requests to the '/user/confirm/<token>' route.
    It receives a unique token that was sent to the user's email address.

    It first tries to confirm the token. If the token is invalid or expired, it flashes a corresponding
    message and redirects the user to the 'unconfirmed' route.

    If the token is valid, it fetches the user associated with the email address extracted from the token.
    If the user's email is already confirmed, it informs the user and redirects them to the homepage.
    If the user's email is not yet confirmed, it sets the user's 'email_confirmed' attribute to True, 
    saves this change in the database, flashes a success message, and redirects the user to the homepage.

    Args:
        token (str): The confirmation token that was sent to the user's email.

    Returns:
        Redirection: Based on the validation of the token and the confirmation status of the user's email,
        it redirects the user to the appropriate route.
    """

    try:
        email = confirm_token(app, token)

    except:
        flash('The confirmation link is invalid or has expired.', 'danger')

        return redirect(url_for('unconfirmed'))

    user = User.query.filter_by(email=email).first_or_404()

    if user.email_confirmed:
        flash('Account already confirmed. Please login.', 'info')

    else:
        user.email_confirmed = True
        db.session.add(user)
        db.session.commit()
        flash('You have confirmed your account.', 'success')

    return redirect(url_for('homepage'))

@app.route('/user/thanks')
def thanks():
    """
    Render a 'Thank You' page.

    This function handles GET requests to the '/user/thanks' route and it doesn't require any input parameters. 
    It is used to display a 'Thank You' message to the user after successful registration.

    Returns:
        Rendered template: Returns the 'thanks.html' template that is used to display the thank you message.
    """

    return render_template('thanks.html')

@app.route('/user/logout')
@login_required
def logout():
    """
    Handle user logout.

    This function handles requests to the '/user/logout' route. It logs out the current user and redirects
    them to the homepage. Note that this route requires the user to be logged in, as enforced by the 
    '@login_required' decorator.

    Returns:
        Werkzeug Response: A response object that redirects the user to the homepage.
    """

    logout_user()

    return redirect(url_for('homepage'))

@app.route('/user/<int:id>')
@login_required
@email_confirmed_required
def show_user(id):
    """
    Display user profile and recent story details.

    This function handles GET requests to the '/user/<int:id>' route. It retrieves the user's 
    profile details, their most recent story, and the steps associated with that story, 
    then displays this information. Note that this route requires the user to be logged in,
    as enforced by the '@login_required' decorator.

    Parameters:
        id (int): The ID of the user whose details are to be shown.

    Returns:
        Rendered template or Werkzeug Response: If the user trying to access the page is the same 
        user as the profile being viewed, it returns the 'users/detail.html' template with 
        the user, story and steps as context variables. 
        If the user trying to access the page is not the same user as the profile being viewed, 
        it redirects the user to the homepage with a failure message.
    """

    user = User.query.get_or_404(id)

    story = (
        Story.query
        .filter_by(author_id=current_user.id)
        .order_by(func.greatest(Story.created_at, Story.accessed_at).desc())
        .first()
        )

    if story is not None:
        steps = StoryStep.query.filter_by(story_id=story.id).all()
    else:
        steps = []

    if current_user.id != id:
        flash("You do not have permission to view this page.", "danger")
        return redirect(url_for('homepage'))

    return render_template('/users/detail.html', user=user, story=story, steps=steps)

@app.route('/user/edit', methods=["GET", "POST"])
@login_required
@email_confirmed_required
def edit_user():
    """
    Handle the editing of user profiles.

    This function handles both GET and POST requests to the '/user/edit' route. 
    For a GET request, it displays a form populated with the current user's details. 
    For a POST request, it validates the form, checks the user's password for security reasons,
    and either updates the user's details or deletes the user, depending on which submit 
    button was clicked. Note that this route requires the user to be logged in,
    as enforced by the '@login_required' decorator.

    Returns:
        Rendered template or Werkzeug Response: For a GET request, it returns the 'users/edit.html' template with the form as a context variable. 
        For a POST request, if form validation and password check succeeds, it redirects the user to the 
        homepage or their profile page (depending on whether the user was deleted or updated).
        If form validation or password check fails, it renders the 'users/edit.html' template again with form errors or a failure message.
    """

    user = User.query.filter_by(id=current_user.id).first()
    form = EditUserForm(request.form, obj=user)

    if request.method == "POST" and form.validate_on_submit():

        password = form.password.data

        if User.authenticate(current_user.username, password):

            if request.form['submit-btn'] == 'delete':

                logout_user()
                db.session.delete(user)
                db.session.commit()

                return redirect(url_for('homepage'))
            
            if request.form['submit-btn'] == 'update':

                user_data = {field.name: field.data for field in form if field.name not in ['username', 'password']}
                for field, value in user_data.items():
                    setattr(user, field, value)
                db.session.commit()  

                flash("Profile updated!", "info") 
                return redirect(url_for('show_user', id=current_user.id))
    
    return render_template('/users/edit.html', form=form)

@app.route('/character/add', methods=["GET", "POST"])
@login_required
@email_confirmed_required
def add_character():
    """
    Handles the creation of new characters.

    This function handles both GET and POST requests to the '/character/add' route. 
    For a GET request, it displays an empty character creation form. 
    For a POST request, it validates the form and, if valid, creates a new character 
    associated with the current logged-in user. Note that this route requires the user to be logged in,
    as enforced by the '@login_required' decorator.

    Returns:
        Rendered template or Werkzeug Response: For a GET request, it returns the 'characters/add.html' template with the form as a context variable. 
        For a POST request, if the form validates, it redirects the user to the characters index page 
        with a success message, otherwise, it re-renders the 'characters/add.html' template with form errors.
    """

    form = CharacterForm()

    if request.method == "POST" and form.validate_on_submit():
         
        character_data = {field.name: getattr(form, field.name).data for field in form}
        character = Character.create_character(character_data, current_user.id)

        db.session.commit()
        flash("Character created!", "info")
        return redirect(url_for('show_characters'))

    return render_template('/characters/add.html', form=form)

@app.route('/character/index', methods=["GET", "POST"])
@login_required
@email_confirmed_required
def show_characters():
    """
    Display the list of characters created by the current user.

    This function handles both GET and POST requests to the '/character/index' route. 
    It retrieves all characters associated with the current logged-in user and renders them 
    on the 'characters/index.html' page. Note that this route requires the user to be logged in,
    as enforced by the '@login_required' decorator.

    Returns:
        Rendered template: 'characters/index.html' template with the list of characters as a context variable 
        and a CharacterForm instance for creating new characters.
    """

    page = request.args.get('page', 1, type=int)
    characters = Character.query.filter_by(user_id=current_user.id).paginate(page=page, per_page=6) 
    form = CharacterForm()

    return render_template('/characters/index.html', characters=characters, form=form)

@app.route('/character/edit/<int:id>', methods=["GET", "POST"])
@login_required
@email_confirmed_required
def edit_character(id):
    """
    Edit the details of a specific character.

    This function handles both GET and POST requests to the '/character/edit/<int:id>' route.
    For a GET request, it displays a form pre-populated with the current details of the character
    specified by the `id`. For a POST request, it validates the form and, if valid, updates the
    character's details. Note that this route requires the user to be logged in, as enforced by
    the '@login_required' decorator. Furthermore, the user can only edit characters that they own.

    Args:
        id (int): The ID of the character to be edited.

    Returns:
        Rendered template or Werkzeug Response: For a GET request, it returns the 'characters/edit.html'
        template with the form as a context variable. For a POST request, if the form validates, it 
        redirects the user to the characters index page with a success message, otherwise, it re-renders 
        the 'characters/edit.html' template with form errors.
    """

    character = Character.query.get_or_404(id)
    form = CharacterForm(obj=character)

    if character and character.user_id == current_user.id:
        if request.method == "POST" and form.validate_on_submit():
        
            form.populate_obj(character)

            db.session.commit()
            flash("Character updated!", "info")

            return redirect(url_for('show_characters'))
        
    else:
        flash("You do not have permission to view this page.", "danger")
        return redirect(url_for('homepage'))
    
    return render_template('/characters/edit.html', form=form)

@app.route('/character/delete/<int:id>', methods=["POST"])
@login_required
@email_confirmed_required
def delete_character(id):
    """
    Delete a specific character associated with the current user.

    This function handles POST requests to the '/character/delete/<int:id>' route. It retrieves 
    the character specified by the `id` and checks whether the current user is the owner of that 
    character. If the user owns the character, the character is deleted from the database and the 
    user is redirected to the character index page with a success message. If the user does not own 
    the character, they are redirected to the homepage with an error message. Note that this route 
    requires the user to be logged in, as enforced by the '@login_required' decorator.

    Args:
        id (int): The ID of the character to be deleted.

    Returns:
        Werkzeug Response: A redirect to the characters index page if the character is deleted, or 
        a redirect to the homepage if the user does not have permission to delete the character.
    """

    character = Character.query.get_or_404(id)

    if character.user_id == current_user.id:
        db.session.delete(character)
        db.session.commit()
        flash("Character deleted.", "info")

        return redirect(url_for('show_characters'))
    
    else:
        flash("You do not have permission to view this page.", "danger")
        return redirect(url_for('homepage'))
    
@app.route('/story/index', methods=["GET", "POST"])
@login_required
@email_confirmed_required
def show_stories():
    """
    Display all stories associated with the current user.

    This function handles both GET and POST requests to the '/story/index' route. It retrieves all
    stories that belong to the current logged-in user and passes them to the 'stories/index.html'
    template for rendering. Note that this route requires the user to be logged in, as enforced by
    the '@login_required' decorator.

    Returns:
        str: A string of HTML rendered by the 'stories/index.html' template, which includes a list
        of all stories associated with the current user.
    """
    page = request.args.get('page', 1, type=int)
    stories = Story.query.filter_by(author_id=current_user.id).order_by((Story.created_at).desc()).paginate(page=page, per_page=6)

    return render_template('/stories/index.html', stories=stories)

@app.route('/story/edit/<int:id>', methods=["GET", "POST"])
@login_required
@email_confirmed_required
def edit_story(id):
    """
    Edit a specific story associated with the current user.

    This function handles GET and POST requests to the '/story/edit/<int:id>' route. It retrieves 
    the story specified by the `id` and checks whether the current user is the author of that 
    story. If the user is the author, it presents a form to edit the story. If the form submission 
    is valid upon POST request, the story is updated in the database. The user is then redirected 
    to the story index page with a success message. If the user is not the author, they are 
    redirected to the homepage with an error message. Note that this route requires the user to be 
    logged in, as enforced by the '@login_required' decorator.

    Args:
        id (int): The ID of the story to be edited.

    Returns:
        Werkzeug Response: A redirect to the story index page if the story is updated, or 
        a redirect to the homepage if the user does not have permission to edit the story. If a GET
        request is made, or the form submission is not valid, it returns an HTML string rendered 
        by the 'stories/edit.html' template.
    """

    story = Story.query.get_or_404(id)
    form = EditStoryForm(obj=story)

    if story.author_id == current_user.id:
        if request.method == "POST" and form.validate_on_submit():
            form.populate_obj(story)

            db.session.commit()
            flash("Story updated!", "info")

            return redirect(url_for('show_stories'))

    else:
        flash("You do not have permission to view this page.", "danger")
        return redirect(url_for('homepage'))
        
    return render_template('/stories/edit.html', form=form)

@app.route('/story/delete/<int:id>', methods=["POST"])
@login_required
@email_confirmed_required
def delete_story(id):
    """
    Delete a specific story associated with the current user.

    This function handles POST requests to the '/story/delete/<int:id>' route. It retrieves the
    story specified by the `id` and checks whether the current user is the author of that story.
    If the user is the author, the story is deleted from the database and the user is redirected 
    to the story index page with a success message. If the user is not the author, they are 
    redirected to the homepage with an error message. Note that this route requires the user to be 
    logged in, as enforced by the '@login_required' decorator.

    Args:
        id (int): The ID of the story to be deleted.

    Returns:
        Werkzeug Response: A redirect to the story index page if the story is deleted, or a 
        redirect to the homepage if the user does not have permission to delete the story.
    """

    story = Story.query.get_or_404(id)

    if story.author_id == current_user.id:
        db.session.delete(story)
        db.session.commit()
        flash("Story deleted.", "info")

        return redirect(url_for('show_stories'))
    
    else:
        flash("You do not have permission to view this page.", "danger")
        return redirect(url_for('homepage'))

@app.route('/story/generate', methods=["GET", "POST"])
@login_required
@email_confirmed_required
def generate_story():
    """
    Handle the story generation process with selected genres and characters.

    This function manages GET and POST requests to the '/story/generate' route. For GET requests, 
    it prepares the genre form by fetching all genres from the database and redirecting to the 
    homepage. For POST requests, it checks if the submitted form is valid. If the form is valid, 
    it increments the user's genre preference count for the selected genres, creates a prompt 
    using the selected genres and characters, and makes an API request to generate the story. The 
    user is then redirected to the user detail page where the new story can be viewed.

    Note that this route requires the user to be logged in, as enforced by the '@login_required' 
    decorator.

    Returns:
        Werkzeug Response: A redirect to the homepage (for GET requests or invalid forms), or a 
        redirect to the user detail page (for successful story generation).
    """

    genres = Genre.query.all()
    form = GenreForm()
    form.genres.choices = [(genre.id, genre.name) for genre in genres]
    
    if request.method == "POST" and form.validate_on_submit():
            selected_genres = form.genres.data
            selected_characters = request.form.getlist('characters')
            genres = [Genre.query.get_or_404(id) for id in selected_genres]

            for genre in genres:
                UserGenre.increment_count(user_id=current_user.id, genre_id=genre.id)

            make_api_request(selected_genres, selected_characters)

            return redirect(url_for('show_user', id=current_user.id))
    
    page = request.args.get('page', 1, type=int)
    characters = Character.query.filter_by(user_id=current_user.id).paginate(page=page, per_page=20)
    
    return render_template('home.html', form=form, characters=characters)

@app.route('/story/view/<int:id>')
@login_required
@email_confirmed_required
def show_story(id):
    """
    Display the specified story by ID for the logged-in user.

    This function manages GET requests to the '/story/view/<id>' route. The function
    fetches a story by its ID and checks if the story was authored by the currently
    logged-in user. If so, it updates the 'accessed_at' attribute of the story with 
    the current date and time and redirects the user to their user detail page, 
    where they can view the selected story. If the story was not authored by the 
    current user, the function redirects the user to the homepage with an error message.
    
    Note that this route requires the user to be logged in, as enforced by the 
    '@login_required' decorator.

    Args:
        id (int): The ID of the story to be displayed.

    Returns:
        Werkzeug Response: A redirect to the user detail page if the story was authored
        by the current user, or a redirect to the homepage with an error message otherwise.
    """

    story = Story.query.get_or_404(id)
    
    if story.author_id == current_user.id:
        story.accessed_at = datetime.utcnow()
        db.session.commit()

        return redirect(url_for('show_user', id=current_user.id))
    
    else:
        flash("You do not have permission to view this page.", "danger")
        return redirect(url_for('homepage'))
    
@app.route('/story/continue/<int:id>', methods=["POST"])
@login_required
@email_confirmed_required
def continue_story(id):
    """
    Handle the process of continuing a story by adding new steps.

    This function manages POST requests to the '/story/continue/<id>' route. It checks if the user 
    has the permission to continue the story (based on the story's author_id). If the user is the 
    author, it adds a new choice to the story using the selected story step's content, commits 
    the choice to the database, and uses the 'next_step' function to determine the new story. 
    The user is then redirected to their user detail page where the updated story can be viewed.
    
    If the story was not authored by the current user or the request method is not "POST", the function 
    redirects the user to the homepage with an error message.

    Note that this route requires the user to be logged in, as enforced by the '@login_required' decorator.

    Args:
        id (int): The ID of the story to be continued.

    Returns:
        Werkzeug Response: A redirect to the user detail page if the story was continued successfully,
        or a redirect to the homepage with an error message otherwise.
    """

    story = Story.query.get_or_404(id)

    if story.author_id != current_user.id:
        flash("You do not have permission to continue this story.", "danger")
        return redirect(url_for('homepage'))

    if request.method == "POST":
    
        step_id = request.form.get('step_id')
        step = StoryStep.query.get(step_id)

        new_choice = Choice(choice_text=step.content, from_step_id=step_id)
        db.session.add(new_choice)
        db.session.commit()

        new_story = next_step(id, new_choice)

        new_choice.to_story_id = new_story.id
        db.session.commit()

        return redirect(url_for('show_user', id=current_user.id))
    
    else:
        flash("You do not have permission to view this page.", "danger")
        return redirect(url_for('homepage'))
    
@app.route('/story/read/<int:id>')
@login_required
@email_confirmed_required
def read_story(id):
    """
    Display the sequence of a story starting from a specified story.

    This function uses the 'get_story_chain' method of the Story model to fetch the chain of stories 
    starting from and including the specified story. It then renders a template with the sequence 
    of stories (referred to as a 'chain').

    Note that this route requires the user to be logged in, as enforced by the '@login_required' decorator.

    Args:
        id (int): The ID of the story from which to start fetching the chain.

    Returns:
        Werkzeug Response: The rendered template for the '/stories/read.html' page with the 
        chain of stories.
    """

    chain = Story.get_story_chain(id)

    return render_template('/stories/read.html', chain=chain)
