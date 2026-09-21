# models/organization.py
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from models import db


class Organization(db.Model):
    __tablename__ = 'organizations'

    organization_id     = db.Column(db.Integer, primary_key=True)
    organization_name   = db.Column(db.String(200), nullable=False)
    email               = db.Column(db.String(150), unique=True, nullable=False, index=True)
    password            = db.Column(db.String(256), nullable=False)
    phone               = db.Column(db.String(20))
    address             = db.Column(db.String(255))
    description         = db.Column(db.Text)
    verification_status = db.Column(db.String(20), default='Pending')
    verification_note   = db.Column(db.Text)
    verification_document = db.Column(db.String(255))
    created_at          = db.Column(db.DateTime, default=datetime.utcnow)

    opportunities = db.relationship('Opportunity', backref='organization',
                                    cascade='all, delete-orphan', lazy=True)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def __repr__(self):
        return f'<Organization {self.organization_name}>'
