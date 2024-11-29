import logging
from sqlalchemy.engine import Engine
from sqlalchemy import event
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_mail import Mail

mail = Mail()

db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    
    app.config.from_object('config.Config')
    
    print(f"Database connected: {app.config['SQLALCHEMY_DATABASE_URI']}")
    
    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    
    with app.app_context():
        from . import models
        db.create_all()
    
    
    from app.routes import main 
    
    app.register_blueprint(main)
    
    
    # Set up SQLAlchemy logging
    logging.basicConfig()
    logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

    @event.listens_for(Engine, "before_cursor_execute")
    def log_sql_query(conn, cursor, statement, parameters, context, executemany):
        logging.info("Executing SQL: %s", statement)
        logging.info("With parameters: %s", parameters)
    
    
    return app