from app import app
from models import db, Genre

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