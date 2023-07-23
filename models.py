from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    """
    Database model for users.

    A user has an id, username, first name, last name, email, password, 
    an optional profile image URL, a timestamp of account creation, 
    and relationships to other tables, including Story, Character, UserGenre, 
    and ChatGPTSession.

    The User class includes methods for user signup and authentication.
    """
    
    __tablename__="users"

    
    bcrypt = Bcrypt()

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.Text, nullable=False, unique=True)
    first_name = db.Column(db.Text, nullable=False)
    last_name = db.Column(db.Text, nullable=False)
    email = db.Column(db.Text, nullable=False, unique=True)
    password = db.Column(db.Text, nullable=False)    
    image_url = db.Column(db.Text, default="/static/images/default-pic.png")
    created_at = db.Column(db.DateTime, default = datetime.utcnow)

    stories = db.relationship('Story', backref='author', cascade="all, delete-orphan")
    characters = db.relationship('Character', backref='user', cascade="all, delete-orphan")
    user_genres = db.relationship('UserGenre', backref='user', cascade="all, delete-orphan")
    chatgpt_sessions = db.relationship('ChatGPTSession', backref='user', cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User #{self.id}: {self.username}, {self.email}"
    
    @classmethod
    def signup(cls, user_data):
        """
        Sign up a new user.

        Hashes the password and saves the user to the database.

        Parameters:
            user_data (dict): User information including username, first name, last name, 
                              email, and password. It may optionally include an image_url.

        Returns:
            User: The newly created User object.
        """
        
        hashed_pwd = cls.bcrypt.generate_password_hash(user_data['password']).decode('UTF-8')

        user = User(
            username = user_data['username'],
            first_name = user_data['first_name'],
            last_name = user_data['last_name'],
            email = user_data['email'],
            password = hashed_pwd
        )
        if user_data.get('image_url'):
            user.image_url = user_data['image_url']

        db.session.add(user)
        return user
    
    @classmethod
    def authenticate(cls, username, password):
        """
        Authenticate a user.

        Checks the entered password against the hashed password in the database.

        Parameters:
            username (str): The user's username.
            password (str): The user's password.

        Returns:
            User|bool: The authenticated User object if authentication is successful; False otherwise.
        """

        user = cls.query.filter_by(username=username).first()

        if user:
            is_auth = cls.bcrypt.check_password_hash(user.password, password)
            if is_auth:
                return user
        
        return False

class Story(db.Model):
    """
    Database model for stories.

    A story has an id, title, starting content, timestamps of creation, update, and access,
    an optional cover image URL, and relationships to other tables, including StoryStep.

    The Story class includes a classmethod for creating a story.
    """

    __tablename__ = 'stories'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text, nullable=False)
    start_content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    accessed_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    img_url = db.Column(db.Text, default='/static/images/library3.png')
    end = db.Column(db.Boolean, default=False)

    author_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'))

    story_steps = db.relationship('StoryStep', backref='story', cascade="all, delete-orphan")
    characters = db.relationship('StoryCharacters', backref='story', cascade="all, delete-orphan", passive_deletes=True)
    choices = db.relationship("Choice", back_populates="story")

    def __repr__(self):
        return f"Story #{self.id}, {self.title}, {self.author_id}"

    @classmethod
    def create_story(cls, title, start_content, author_id, end=False):
        """
        Create a new story.

        Saves the new story to the database.

        Parameters:
            title (str): The story's title.
            start_content (str): The starting content for the story.
            author_id (int): The ID of the author of the story.

        Returns:
            Story: The newly created Story object.
        """

        story = Story(
            title = title,
            start_content = start_content,
            author_id = author_id,
            end = end
        )
        
        db.session.add(story)
        db.session.commit()
        return story

    @classmethod
    def get_story_chain(cls, id):
        """
        Retrieves the chain of stories starting from the specified story.

        This method starts at the given story and then iteratively follows the choices to gather 
        a chain of stories. The chain ends when a story has no further choices that lead to it.

        Args:
            cls (Class): The class that this method is a part of.
            id (int): The ID of the story to start the search from.

        Returns:
            list: A list of Story objects representing the chain of stories.
        """
        story = cls.query.get(id)
        if not story:
            raise ValueError(f"Story with id {id} not found")

        chain = [story]

        while True:
            choice = Choice.query.filter_by(to_story_id=story.id).first()
            if not choice:
                return chain

            step = choice.from_step
            if not step:
                raise ValueError(f"Step for choice with id {choice.id} not found")

            story = step.story
            if not story:
                raise ValueError(f"Story for step with id {step.id} not found")

            chain.insert(0, story)

class Choice(db.Model):
    """
    Database model for choices within a story.

    A choice has an id, choice text, timestamp of creation, and foreign keys linking it to a story step and a genre.
    """

    __tablename__ = 'choices'

    id = db.Column(db.Integer, primary_key=True)
    choice_text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    story_id = db.Column(db.Integer, db.ForeignKey('stories.id', ondelete='CASCADE'))
    from_step_id = db.Column(db.Integer, db.ForeignKey('story_steps.id', ondelete='CASCADE'))
    to_story_id = db.Column(db.Integer, db.ForeignKey('story_steps.id', ondelete='CASCADE'))

    story = db.relationship("Story", back_populates="choices")

class StoryStep(db.Model):
    """
    Database model for steps within a story.

    A story step has an id, content, timestamp of creation, and a foreign key linking it to a story.
    """

    __tablename__ = 'story_steps'

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    story_id = db.Column(db.Integer, db.ForeignKey('stories.id', ondelete='CASCADE'))
    choices_from = db.relationship('Choice', backref='from_step',
                                   cascade="all, delete-orphan",
                                   primaryjoin='Choice.from_step_id==StoryStep.id')
    choices_to = db.relationship('Choice', backref='to_story',
                                 cascade='all, delete-orphan',
                                 primaryjoin='Choice.to_story_id==StoryStep.id')
    
    def __repr__(self):
        return f"content: {self.content}, story.id: {self.story_id}"

class Genre(db.Model):
    """
    Database model for genres.

    A genre has an id, name, and a relationship to the UserGenre table.
    """

    __tablename__ = 'genres'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)

    user_genres = db.relationship('UserGenre', backref='genre', cascade="all, delete-orphan")

class StoryCharacters(db.Model):
    """
    Database model for characters in stories.
    
    A story_characters has an id, a story id, and a character id.
    """
    __tablename__ = 'story_characters'

    id = db.Column(db.Integer, primary_key=True)
    story_id = db.Column(db.Integer, db.ForeignKey('stories.id', ondelete='CASCADE'))
    character_id = db.Column(db.Integer, db.ForeignKey('characters.id', ondelete='CASCADE'))

class Character(db.Model):
    """
    Database model for characters.

    A character has an id, name, description, an optional image URL, timestamp of creation, and a foreign key linking it to a user.

    The Character class includes a classmethod for creating a character.
    """

    __tablename__ = 'characters'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.Text, default="/static/images/default-pic.png")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'))

    stories = db.relationship('StoryCharacters', backref='character', cascade="all, delete-orphan", passive_deletes=True)

    def __repr__(self):
        return f"Character# {self.id}, {self.name}"

    @classmethod
    def create_character(slf, character_data, user_id):
        """
        Create a new character.

        Saves the new character to the database.

        Parameters:
            character_data (dict): Character information including name and description. 
                                   It may optionally include an image_url.
            user_id (int): The ID of the user who created the character.

        Returns:
            Character: The newly created Character object.
        """

        character = Character(
            name = character_data['name'],
            description = character_data['description'],
            user_id = user_id
        )

        if character_data.get('image_url'):
            character.img_url = character_data['image_url']

        db.session.add(character)
        return character

class UserGenre(db.Model):
    """
    Database model for user's preferred genres.

    UserGenre has two primary keys: user_id and genre_id, and a count for the number of times a user selects a particular genre.

    The UserGenre class includes a classmethod for incrementing the count of a genre for a user.
    """

    __tablename__ = 'user_genres'

    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    genre_id = db.Column(db.Integer, db.ForeignKey('genres.id', ondelete='CASCADE'), primary_key=True)

    count = db.Column(db.Integer, default=0)

    @classmethod
    def increment_count(cls, user_id, genre_id):
        """
        Increment the genre count for a user.

        If the user has not selected the genre before, a new record is created in the database with a count of 1.
        If the user has selected the genre before, the existing count is incremented.

        Parameters:
            user_id (int): The ID of the user.
            genre_id (int): The ID of the genre.

        Returns:
            UserGenre: The updated UserGenre object.
        """

        user_genre = cls.query.filter_by(user_id=user_id, genre_id=genre_id).first()

        if not user_genre:
            user_genre = cls(user_id=user_id, genre_id=genre_id, count=1)
            db.session.add(user_genre)
        else:
            user_genre.count += 1

        db.session.commit()
        return user_genre

class ChatGPTSession(db.Model):
    """
    Database model for ChatGPT sessions.

    A ChatGPTSession has an id, session id, timestamp of creation, and foreign keys linking it to a user and a story.
    """

    __tablename__= 'chatgpt_sessions'

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'))
    story_id = db.Column(db.Integer, db.ForeignKey('stories.id', ondelete='CASCADE'))

def connect_db(app):
    """
    Connects the application to the database.

    Parameters:
        app (Flask app): The Flask application to connect to the database.
    """

    db.app = app
    db.init_app(app)