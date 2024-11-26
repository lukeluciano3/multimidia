from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from models.user import db, User

class Video(db.Model):
    __tablename__ = 'videos'
    
    id = db.Column(db.Integer, primary_key=True)
    original_filename = db.Column(db.String(200), nullable=False)
    filename = db.Column(db.String(200), nullable=False, unique=True)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user = db.relationship('User', backref='videos')

    def __init__(self, original_filename, filename, user_id):
        self.original_filename = original_filename
        self.filename = filename
        self.user_id = user_id