import uuid
from selfservice.models import RecoverySession, ResetToken, PhoneVerification
from selfservice.utilities.general import is_expired
from selfservice import db
import random

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
		session=session.id)
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
