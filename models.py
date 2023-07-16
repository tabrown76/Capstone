from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from datetime import datetime

db = SQLAlchemy()

bcrypt = Bcrypt()

class User(db.Model):
    __tablename__="users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.Text, nullable=False, unique=True)
    first_name = db.Column(db.Text, nullable=False)
    last_name = db.Column(db.Text, nullable=False)
    email = db.Column(db.Text, nullable=False, unique=True)
    password_hash = db.Column(db.Text, nullable=False)    
    image_url = db.Column(db.Text, default="/static/images/default-pic.png")
    created_at = db.Column(db.DateTime, default = datetime.utcnow)

    stories = db.relationship('Story', backref='author')
    characters = db.relationship('Character', backref='user')
    user_genres = db.relationship('UserGenre', backref='user')
    chatgpt_sessions = db.relationship('ChatGPTSession', backref='user')

    def __repr__(self):
        return f"<User #{self.id}: {self.username}, {self.email}"
    
    @classmethod
    def signup(cls, username, first_name, last_name, email, password_hash, image_url, created_at):
        
        hashed_pwd = bcrypt.generate_password_hash(password_hash).decode('UTF-8')

        user = User(
            username = username,
            first_name = first_name,
            last_name = last_name,
            email = email,
            password_hash = hashed_pwd,
            image_url = image_url,
            created_at = created_at
        )

        db.session.add(user)
        return user
    
    @classmethod
    def authenticate(cls, username, password):

        user = cls.query.filter_by(username=username).first()

        if user:
            is_auth = bcrypt.check_password_hash(user.password_hash, password)
            if is_auth:
                return user
        
        return False

class Story(db.Model):
    __tablename__ = 'stories'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text, nullable=False)
    start_content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    character_id = db.Column(db.Integer, db.ForeignKey('characters.id'))

    story_steps = db.relationship('StoryStep', backref='story')

    @classmethod
    def create_story(cls, title, start_content, created_at):

        story = Story(
            title = title,
            start_content = start_content,
            created_at = created_at
        )
        
        db.session.add(story)
        return story


class StoryStep(db.Model):
    __tablename__ = 'story_steps'

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    story_id = db.Column(db.Integer, db.ForeignKey('stories.id'))

class Choice(db.Model):
    __tablename__ = 'choices'

    id = db.Column(db.Integer, primary_key=True)
    choice_text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    from_step_id = db.Column(db.Integer, db.ForeignKey('story_steps.id'))
    to_step_id = db.Column(db.Integer, db.ForeignKey('story_steps.id'))
    genre_id = db.Column(db.Integer, db.ForeignKey('genres.id'))

class Genre(db.Model):
    __tablename__ = 'genres'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)

    user_genres = db.relationship('UserGenre', backref='genre')

class Character(db.Model):
    __tablename__ = 'characters'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.Text, default="/static/images/default-pic.png")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    @classmethod
    def create_character(slf, name, description, img_url, created_at):

        character = Character(
            name = name,
            description = description,
            img_url = img_url,
            created_at = created_at
        )

        db.session.add(character)
        return character

class UserGenre(db.Model):
    __tablename__ = 'user_genres'

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    genre_id = db.Column(db.Integer, db.ForeignKey('genres.id'), primary_key=True)

    count = db.Column(db.Integer, default=0)

    @classmethod
    def increment_count(cls, user_id, genre_id):

        user_genre = cls.query.filter_by(user_id=user_id, genre_id=genre_id).first()

        if not user_genre:
            user_genre = cls(user_id=user_id, genre_id=genre_id, count=1)
            db.session.add(user_genre)
        else:
            user_genre.count += 1

        db.session.commit()
        return user_genre

class ChatGPTSession(db.Model):
    __tablename__= 'chatgpt_sessions'

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    story_id = db.Column(db.Integer, db.ForeignKey('stories.id'))

def connect_db(app):
    """Connect to database."""

    db.app = app
    db.init_app(app)