# models/experience.py
from models import db


class Experience(db.Model):
    """One work-experience record belonging to a student.

    Each record is tied to its own technology/field so the recommendation
    system can tell *what* the experience is in (e.g. Python vs Java).
    """
    __tablename__ = 'experiences'

    experience_id = db.Column(db.Integer, primary_key=True)
    student_id    = db.Column(db.Integer,
                              db.ForeignKey('students.student_id'),
                              nullable=False, index=True)
    role          = db.Column(db.String(150), nullable=False)
    company       = db.Column(db.String(150), nullable=False)
    technology    = db.Column(db.String(100), nullable=False)
    years         = db.Column(db.Float, default=0)
    description   = db.Column(db.Text)

    def __repr__(self):
        return f'<Experience {self.technology} {self.years}y student={self.student_id}>'
