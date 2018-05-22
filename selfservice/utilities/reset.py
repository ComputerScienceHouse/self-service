import requests
import random
import uuid
import ldap

from selfservice.models import RecoverySession, ResetToken, PhoneVerification
from selfservice.utilities.general import is_expired
from selfservice import db, app


class TokenAlreadyExists(Exception):
    pass

def generate_token(session):
	# Generate a random UUID for reset token.
	token = str(uuid.uuid4())

	# Verify that this session creates only one token.
	previous = ResetToken.query.filter_by(session=session.id).first()
	if previous:
		raise TokenAlreadyExists()

	# Create the object in the database.
	reset = ResetToken(
		username=session.username,
		token=token,
		session=session.id,
		used=False)
	db.session.add(reset)
	db.session.commit()

	return(token)

def generate_pin(session):
	# Generate a random UUID for reset token.
	token = f'{random.randrange(1, 10**6):06}'

	# Verify that this session creates only one token.
	previous = ResetToken.query.filter_by(session=session.id).first()
	if previous:
		raise TokenAlreadyExists()

	# Create the object in the database.
	reset = PhoneVerification(
		code=token,
		session=session.id)
	db.session.add(reset)
	db.session.commit()

	return(token)

def valid_token(token_id):
	token = ResetToken.query.filter_by(token=token).first()

	if token:
		if is_expired(token.created, 30):
			return False
		return True
	else:
		return False


def passwd_reset(username, password):
	# Create LDAP admin session to perform initial reset.
	dn = "uid={},cn=users,cn=accounts,dc=csh,dc=rit,dc=edu".format(
		username)
	
	l = ldap.initialize("ldaps://stone.csh.rit.edu")
	l.simple_bind_s(app.config["LDAP_BIND_DN"], app.config["LDAP_BIND_PW"])
	l.modify_s(
		dn, [(ldap.MOD_REPLACE,'userPassword',[password.encode()])]
		)

	# FreeIPA automatically expires the password set through the previous
	# method, so we need to use their password change API to get past that.
	change = requests.post(
		"https://stone.csh.rit.edu/ipa/session/change_password",
		data={
			"user": username,
			"old_password": password,
			"new_password": password})

