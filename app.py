from flask import Flask, render_template, redirect, session, url_for, request, flash
from flask_login import LoginManager, login_required, current_user, logout_user, login_user
from models import db, connect_db, User, Story, StoryStep, Choice, Genre, Character, UserGenre, ChatGPTSession
from forms import AddUserForm, LoginForm, EditUserForm, GenreForm, CharacterForm
from sqlalchemy.exc import IntegrityError
import os
import openai
import config

app = Flask (__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql:///ai_venture"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = True
app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY")
openai.api_key = os.getenv("OPENAI_API_KEY")

login_manager = LoginManager()
login_manager.init_app(app)

connect_db(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/', methods=["GET", "POST"])
def homepage():
    
    if current_user.is_authenticated:

        form = GenreForm()
        genres = Genre.query.all()
        form.genres.choices = [(g.id, g.name) for g in genres]
        
        return render_template('home.html', id=current_user.id, form=form)
    else:
        return render_template('home-anon.html')

@app.route('/user/signup', methods=["GET", "POST"])
def signup():

    form = AddUserForm()

    if request.method == "POST" and form.validate_on_submit():
        user_data = {field.name: getattr(form, field.name).data for field in form}
        new_user = User.signup(user_data)

        db.session.commit()
        login_user(new_user)        
        flash("Sign up successful!", "success")

        return redirect(url_for('homepage'))


    return render_template('/users/signup.html', form=form)

@app.route('/user/login', methods=["GET", "POST"])
def login():

    form = LoginForm()

    if request.method == "POST" and form.validate_on_submit():
        user = User.authenticate(form.username.data,
                                 form.password.data)
        
        if user:
            login_user(user)
            flash(f"Welcome back, {user.username}!", "success")
            return redirect(url_for('homepage', id=user.id))
        
        flash("Invalid Username/Password combination.", "danger")

    return render_template('/users/login.html', form=form)

@app.route('/user/logout')
@login_required
def logout():

    logout_user()
    return redirect(url_for('homepage'))

@app.route('/user/<int:id>')
@login_required
def show_user(id):

    user = User.query.get_or_404(id)

    if current_user.id != id:
        flash("You do not have permission to view this page.", "danger")
        return redirect(url_for('homepage', id=current_user.id))

    return render_template('/users/detail.html', user=user)

@app.route('/user/edit', methods=["GET", "POST"])
@login_required
def edit_user():

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
            
            else:
                user_data = {field.name: field.data for field in form if field.name != 'password'}
                for field, value in user_data.items():
                    setattr(user, field, value)
                db.session.commit()  
                flash("Profile updated!", "info")      

                return redirect(url_for('show_user', id=current_user.id))
    
    return render_template('/users/edit.html', form=form)

@app.route('/character/add', methods=["GET", "POST"])
@login_required
def add_character():

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
def show_characters():

    characters = Character.query.filter_by(user_id=current_user.id).all()
    form = CharacterForm()

    return render_template('/characters/index.html', characters=characters, form=form)

@app.route('/character/edit/<int:id>', methods=["GET", "POST"])
@login_required
def edit_character(id):

    form = CharacterForm()
    character = Character.query.get(id)

    if request.method == "POST" and form.validate_on_submit():
        if character and character.user_id == current_user.id:
            character_data = {field.name: field.data for field in form}
            for field, value in character_data.items():
                setattr(character, field, value)

            db.session.commit()
            flash("Character updated!", "info")

            return redirect(url_for('show_characters'))
    
    form.name.data = character.name
    form.description.data = character.description
    form.image_url.data = character.img_url

    return render_template('/characters/edit.html', form=form)

@app.route('/character/delete/<int:id>', methods=["POST"])
@login_required
def delete_character(id):

    character = Character.query.get(id)

    if character.user_id == current_user.id:
        db.session.delete(character)
        db.session.commit()
        flash("Character deleted.", "info")

        return redirect(url_for('show_characters'))