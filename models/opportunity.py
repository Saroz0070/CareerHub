# models/opportunity.py
from datetime import datetime
from models import db


class Opportunity(db.Model):
    __tablename__ = 'opportunities'

    opportunity_id      = db.Column(db.Integer, primary_key=True)
    organization_id     = db.Column(db.Integer,
                                    db.ForeignKey('organizations.organization_id'),
                                    nullable=False)
    title               = db.Column(db.String(200), nullable=False)
    description         = db.Column(db.Text, nullable=False)
    opportunity_type    = db.Column(db.String(50), nullable=False)
    required_skills     = db.Column(db.Text)
    location            = db.Column(db.String(150))
    salary              = db.Column(db.String(100))
    deadline            = db.Column(db.Date)
    experience_required = db.Column(db.Integer, default=0)
    created_at          = db.Column(db.DateTime, default=datetime.utcnow)

    applications = db.relationship('Application', backref='opportunity',
                                   cascade='all, delete-orphan', lazy=True)

    def __repr__(self):
        return f'<Opportunity {self.title}>'
