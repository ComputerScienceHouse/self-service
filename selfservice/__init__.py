import os
import uuid

from csh_ldap import CSHLDAP

from flask import Flask, render_template, request, redirect, url_for
from flask_recaptcha import ReCaptcha
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

from selfservice.utilities.general import is_expired

app = Flask(__name__)

if os.path.exists(os.path.join(os.getcwd(), "config.py")):
    app.config.from_pyfile(os.path.join(os.getcwd(), "config.py"))
else:
    app.config.from_pyfile(os.path.join(os.getcwd(), "config.env.py"))

# Create the database session and import models.
db = SQLAlchemy(app)
from selfservice.models import *
migrate = Migrate(app, db)

# Create recaptcha object
recaptcha = ReCaptcha()
recaptcha.init_app(app)

# Connect to LDAP
ldap = CSHLDAP(app.config['LDAP_BIND_DN'], app.config['LDAP_BIND_PW'])

# Now, that we have everything configured we can grab
# the utilities we need.

from selfservice.utilities.ldap import verif_methods

# Flask Routes

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/recovery', methods=['POST'])
def create_session():

	if recaptcha.verify():

		# Generate a random UUID for session object.
		session_id = str(uuid.uuid4())

		# Create the object in the database.
		session = RecoverySession(
			id=session_id,
			username=request.form["username"])
		db.session.add(session)
		db.session.commit()

		# Redirect the user to thier session.
		return redirect("/recovery/" + session_id)


@app.route('/recovery/<recovery_id>')
def verify_identity(recovery_id):

	# Retrieve the session object.
	session = RecoverySession.query.filter_by(id=recovery_id).first()

	# Make sure it isn't expired.
	if is_expired(session.created, 10):
		return redirect("/")

	return render_template('options.html',
		username = session.username,
		methods = verif_methods(session.username))
