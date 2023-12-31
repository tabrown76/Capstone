from app import app
from models import db, Genre, User

with app.app_context():
    db.drop_all()
    db.create_all()

    genres = [
        "Adventure", 
        "Fantasy",
        "Science Fiction",
        "Mystery",
        "Historical Fiction",
        "Realistic Fiction",
        "Contemporary Fiction",
        "Young Adult (YA)",
        "Children's Literature",
        "Fairy Tale/ Folklore",
        "Coming of Age",
        "Dystopian",
        "Inspirational",
        "Drama",
        "Magical Realism",
        "Paranormal",
        "Biography/Autobiography",
        "Educational"
    ]

    def add_genres():
        for genre in genres:
            new_genre = Genre(name=genre)
            db.session.add(new_genre)
        db.session.commit()

    if __name__ == "__main__":
        add_genres()

    dummy_user_data = {
        'username': 'dummyUser',
        'first_name': 'Dummy',
        'last_name': 'User',
        'email': 'dummyUser@example.com',
        'password': 'aA123!@#',
        'image_url': '/static/images/default-pic.png'
    }
    
    dummy_user = User.signup(dummy_user_data)
    db.session.add(dummy_user)
    db.session.commit()
