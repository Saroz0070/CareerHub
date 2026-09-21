# models/__init__.py
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from models.student import Student          # noqa: E402, F401
from models.organization import Organization  # noqa: E402, F401
from models.opportunity import Opportunity  # noqa: E402, F401
from models.application import Application  # noqa: E402, F401
