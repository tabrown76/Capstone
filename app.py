from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, login_required, current_user, logout_user, login_user
from models import db, connect_db, User, Story, StoryStep, Choice, Genre, Character, UserGenre, ChatGPTSession
from forms import AddUserForm, LoginForm, EditUserForm, GenreForm, CharacterForm, EditStoryForm
from api import create_prompt, make_api_request
from sqlalchemy import func
import os
import openai
import config

app = Flask (__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql:///ai_venture"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = True
app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY")

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
        form.genres.choices = [(genre.id, genre.name) for genre in genres]
        characters = Character.query.filter_by(user_id=current_user.id).all()           
        
        return render_template('home.html', id=current_user.id, form=form, characters=characters)
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
            return redirect(url_for('homepage'))
        
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

    story = Story.query.order_by(func.greatest(Story.created_at, Story.updated_at).desc()).first()
    steps = StoryStep.query.filter_by(story_id=story.id).all()

    if current_user.id != id:
        flash("You do not have permission to view this page.", "danger")
        return redirect(url_for('homepage'))

    return render_template('/users/detail.html', user=user, story=story, steps=steps)

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

    character = Character.query.get_or_404(id)
    form = CharacterForm(obj=character)

    if request.method == "POST" and form.validate_on_submit():
        if character and character.user_id == current_user.id:
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
def delete_character(id):

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
def show_stories():

    stories = Story.query.filter_by(author_id=current_user.id).all()

    return render_template('/stories/index.html', stories=stories)

@app.route('/story/edit/<int:id>', methods=["GET", "POST"])
@login_required
def edit_story(id):

    story = Story.query.get_or_404(id)
    form = EditStoryForm(obj=story)

    if request.method == "POST" and form.validate_on_submit():
        if story.author_id == current_user.id:
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
def delete_story(id):

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
def generate_story():

    genres = Genre.query.all()
    form = GenreForm()
    form.genres.choices = [(genre.id, genre.name) for genre in genres]
    
    if request.method == "POST" and form.validate_on_submit():
            selected_genres = form.genres.data
            selected_characters = request.form.getlist('characters')
            genres = [Genre.query.get_or_404(id) for id in selected_genres]

            for genre in genres:
                UserGenre.increment_count(user_id=current_user.id, genre_id=genre.id)

            prompt = create_prompt(selected_genres, selected_characters)
            make_api_request(prompt)

            return redirect(url_for('show_user', id=current_user.id))
    
    return redirect(url_for('homepage'))

@app.route('/story/view/<int:id>')
@login_required
def show_story(id):

    story = Story.query.get_or_404(id)
    
    story.title = story.title
    db.session.commit()

    return redirect(url_for('show_user', id=current_user.id))