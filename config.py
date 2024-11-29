import os
from secrets_info import MAIL_PASSWORD

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'uwiuwiuwi')
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(BASE_DIR, 'uwidormfinder.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = True
    
    # Flask-Mail configuration
    MAIL_SERVER = 'smtp.office365.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    MAIL_USERNAME = 'damion.henry1208@outlook.com'
    MAIL_PASSWORD = MAIL_PASSWORD
    MAIL_DEFAULT_SENDER = ('UWI Dorm Finder', 'damion.henry1208@outlook.com')