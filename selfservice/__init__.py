import os

from flask import Flask, render_template

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask(__name__)

if os.path.exists(os.path.join(os.getcwd(), "config.py")):
    app.config.from_pyfile(os.path.join(os.getcwd(), "config.py"))
else:
    app.config.from_pyfile(os.path.join(os.getcwd(), "config.env.py"))

# Create the database session and import models.
db = SQLAlchemy(app)
from selfservice.models import *
migrate = Migrate(app, db)

@app.route('/')
def hello_world():
        return render_template('index.html')
