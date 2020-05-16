from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def create_app():
    """Construct the core application."""
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_object('config.Config')
    db.init_app(app)

    with app.app_context():
        db.create_all()  # Create database tables for our data models
        from . import auth
        app.register_blueprint(auth.bp)
        from . import admin
        app.register_blueprint(admin.bp)
        from . import mod
        app.register_blueprint(mod.bp)
        from . import mail
        app.register_blueprint(mail.bp)
        app.add_url_rule('/', endpoint='index')
        auth.init_app(app);
        return app
