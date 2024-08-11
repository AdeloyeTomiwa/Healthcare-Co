from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import Index
from sqlalchemy import func, ForeignKey
from datetime import datetime

from db import db


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(600), nullable=False)
    

    def __repr__(self):
        return f"<User {self.username}>"
    
    def set_password(self, password):
        """Hash the password and store it."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check if the given password matches the hashed password."""
        return check_password_hash(self.password_hash, password)
    

class Workout(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    image_path = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False, index=True)

    def __repr__(self):
        return f"<Workout {self.name}>"
    
# Define the index after
Index('idx_workouts_category', Workout.category)


class Article(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False, index=True)
    image_path = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=func.now())

    def __repr__(self):
        return f"<Article {self.title}>"

# Define the index
Index('idx_articles_category', Article.category)


class Activity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, ForeignKey('user.id'), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    weight = db.Column(db.Float, nullable=False)
    height = db.Column(db.Float, nullable=False)
    activity_type = db.Column(db.String(50), nullable=False)
    duration = db.Column(db.Integer, nullable=False)
    intensity = db.Column(db.String(10), nullable=False)
    resting_heart_rate = db.Column(db.Integer, nullable=False)
    exercise_heart_rate = db.Column(db.Integer, nullable=False)
    body_fat_percentage = db.Column(db.Float, nullable=False)
    muscle_mass = db.Column(db.Float, nullable=False)
    water_intake = db.Column(db.Float, nullable=False)
    registered_at = db.Column(db.DateTime, default=func.now())

    def __repr__(self):
        return f"<Activity {self.activity_type} by User {self.user_id}>"

# Define the index
Index('idx_user_id', Activity.user_id)


class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Contact {self.name} - {self.email}>"