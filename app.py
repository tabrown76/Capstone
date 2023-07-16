from flask import Flask, render_template, redirect, session, url_for
from flask_login import LoginManager, login_required, current_user, logout_user
from config import auth_key
from models import db, connect_db, User, Story, StoryStep, Choice, Genre, Character, UserGenre, ChatGPTSession

app = Flask (__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql:///ai_venture"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = True
app.config["SECRET_KEY"] = auth_key

login_manager = LoginManager()
login_manager.init_app(app)

connect_db(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def homepage():

    if current_user.is_authenticated:
        return render_template('dashboard.html', user=current_user)
    else:
        return render_template('index.html')

@app.route('/user/signup')
def signup():
    return render_template('signup.html')

@app.route('/user/login')
def login():
    return render_template('index.html')

@app.route('/user/logout')
@login_required
def logout():

    logout_user()
    return redirect(url_for('homepage'))

@app.route('/user/<int:id>')
@login_required
def user_show(id):

    user = User.query.get_or_404(id)
    return render_template('index.html', user=user)