# config.py
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-careerhub-2024')

    # Defaults to a local SQLite file so the app runs out of the box with
    # zero setup. For MySQL, set the DATABASE_URL environment variable, e.g.:
    #   DATABASE_URL=mysql+pymysql://user:password@localhost:3306/careerhub
    # (PyMySQL is already listed in requirements.txt.)
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL', f"sqlite:///{os.path.join(BASE_DIR, 'careerhub.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB
    ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}

    ADMIN_EMAIL    = os.environ.get('ADMIN_EMAIL', 'admin@careerhub.com')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')

    # Optional Gmail SMTP
    MAIL_SERVER   = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT     = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS  = os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', '')
    MAIL_SENDER   = os.environ.get('MAIL_SENDER', os.environ.get('MAIL_USERNAME', ''))
    MAIL_ENABLED  = bool(
        os.environ.get('MAIL_USERNAME') and os.environ.get('MAIL_PASSWORD')
    )
