import os
import uuid

from csh_ldap import CSHLDAP

from flask import Flask, render_template, request, redirect, url_for, flash
from flask_recaptcha import ReCaptcha
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate, upgrade
from alembic import command

from selfservice.utilities.general import is_expired, email_recovery, phone_recovery


app = Flask(__name__)

if os.path.exists(os.path.join(os.getcwd(), "config.py")):
    app.config.from_pyfile(os.path.join(os.getcwd(), "config.py"))
else:
    app.config.from_pyfile(os.path.join(os.getcwd(), "config.env.py"))

# Create the database session and import models.
db = SQLAlchemy(app)
from selfservice.models import *
migrate = Migrate(app, db)

if not os.path.exists(os.path.join(os.getcwd(), "data.db")):
	with app.app_context():
		upgrade()

# Create recaptcha object
recaptcha = ReCaptcha()
recaptcha.init_app(app)

# Connect to LDAP
ldap = CSHLDAP(app.config['LDAP_BIND_DN'], app.config['LDAP_BIND_PW'])

# Now, that we have everything configured we can grab
# the utilities we need.
from selfservice.utilities.reset import generate_token, generate_pin, TokenAlreadyExists
from selfservice.utilities.ldap import verif_methods

# Flask Routes

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/recovery', methods=['POST'])
def create_session():

	if recaptcha.verify():

		# If we can't find an account, flash error.
		try:
			ldap.get_member(request.form["username"], True)
		except KeyError:
			flash("Uh oh, either that account doesn't exist or we don't have " +\
				  "a way to verify your identity. Make sure you entered the " +\
				  "correct username or contact an RTP (rtp@csh.rit.edu).")
			return redirect("/")

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
		flash("Sorry, your session has expired.")
		return redirect("/")


	return render_template('options.html',
		username = session.username,
		recovery_id = recovery_id,
		methods = verif_methods(session.username))


@app.route('/recovery/<recovery_id>/<method>')
def method_selection(recovery_id, method):
	# Parse expected URL paramters.
	index = request.args.get('index', default = 0, type = int)
	carrier = request.args.get('carrier', default = '', type = str)

	# Retrieve the session object.
	session = RecoverySession.query.filter_by(id=recovery_id).first()
	methods = verif_methods(session.username)

	# Make sure it isn't expired.
	if is_expired(session.created, 10):
		flash("Sorry, your session has expired.")
		return redirect("/")

	
	# Get Method
	if method == "email":
		# Generate a random UUID for reset token.
		try:
			token = generate_token(session)
		except TokenAlreadyExists:
			flash("This session has already been used to generate an " +\
				  "email recovery token. Please wait for the session to " +\
				  "expire and try again or contact an RTP.")
			return redirect("/")

		rec_email = methods["email"][index]["data"]

		try:
			email_recovery(
				username = session.username,
				address = rec_email,
				token = token)
			return render_template('success.html')
		except:
			flash("Uh oh, something went wrong. Please try again later.")
			return redirect("/")

	elif method == "phone" and not carrier:
		return render_template('phone.html',
			phone = methods["phone"][index]["display"][-4:],
			recovery_id = session.id,
			index = index,
			username = session.username,
			choose_carrier = True)

	elif method == "phone" and carrier:
		try:
			token = generate_pin(session)
		except TokenAlreadyExists:
			flash("This session has already been used to generate a " +\
				  "phone recovery token. Please wait for the session to " +\
				  "expire and try again or contact an RTP.")
			return redirect("/")

		try:
			phone_recovery(
				phone = methods["phone"][index]["data"],
				carrier = carrier,
				token = token)
			return render_template('phone.html',
				recovery_id = session.id,
				username = session.username,
				choose_carrier = False)
		except:
			flash("Uh oh, something went wrong. Please try again later.")
			return redirect("/")


@app.route('/recovery/<recovery_id>/phone/verify', methods=['POST'])
def verify_phone(recovery_id):
	session = RecoverySession.query.filter_by(id=recovery_id).first()
	token = PhoneVerification.query.filter_by(session=recovery_id).first()

	if request.form['verify'] == token.code:
		token = ResetToken.query.filter_by(session=recovery_id).first()
		if not token:
			token = generate_token(session)
		return redirect("/reset?token=" + token)
	else:
		flash("Your verification code did not match, sorry!")
		return redirect("/")
		
