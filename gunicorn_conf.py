"""Gunicorn configuration for self-service application."""

import os

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate, upgrade
from flask import Flask

app = Flask(__name__)

if os.path.exists(os.path.join(os.getcwd(), "config.py")):
    app.config.from_pyfile(os.path.join(os.getcwd(), "config.py"))
else:
    app.config.from_pyfile(os.path.join(os.getcwd(), "config.env.py"))

# Create the database session and import models.
db = SQLAlchemy(app)
from selfservice.models import *  # noqa: F403,E402  # pylint: disable=wrong-import-position,unused-wildcard-import,wildcard-import
migrate = Migrate(app, db)


def on_starting(_server):  # pylint: disable=missing-function-docstring
    if not os.path.exists(os.path.join(os.getcwd(), "data.db")):
        with app.app_context():
            upgrade()
