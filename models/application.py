# models/application.py
from datetime import datetime
from models import db


class Application(db.Model):
    __tablename__ = 'applications'

    application_id  = db.Column(db.Integer, primary_key=True)
    student_id      = db.Column(db.Integer,
                                db.ForeignKey('students.student_id'),
                                nullable=False)
    opportunity_id  = db.Column(db.Integer,
                                db.ForeignKey('opportunities.opportunity_id'),
                                nullable=False)
    status          = db.Column(db.String(20), default='Pending')
    applied_at      = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('student_id', 'opportunity_id',
                            name='uq_student_opportunity'),
    )

    def __repr__(self):
        return f'<Application {self.application_id}>'
