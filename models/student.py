# models/student.py
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from models import db


class Student(db.Model):
    __tablename__ = 'students'

    student_id  = db.Column(db.Integer, primary_key=True)
    full_name   = db.Column(db.String(150), nullable=False)
    email       = db.Column(db.String(150), unique=True, nullable=False, index=True)
    password    = db.Column(db.String(256), nullable=False)
    phone       = db.Column(db.String(20))
    address     = db.Column(db.String(255))
    education   = db.Column(db.String(255))
    skills      = db.Column(db.Text)
    interests   = db.Column(db.Text)
    experience  = db.Column(db.Integer, default=0)
    resume      = db.Column(db.String(255))
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    applications = db.relationship('Application', backref='student',
                                   cascade='all, delete-orphan', lazy=True)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def __repr__(self):
        return f'<Student {self.email}>'
