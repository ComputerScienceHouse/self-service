"""
Functions dealing with application specific password generation and handling
"""

from passlib.hash import sha512_crypt as sha512
from xkcdpass import xkcd_password as xp

from selfservice.utilities.keycloak import OTPAlreadyConfigured
from selfservice.models import AppSpecificPassword
from selfservice import db


def _generate_passwd(length=4):
	"""
    Create an XKCD style (correct-horse-battery-staple) password.

    Keyword arguments:
    length -- Number of words to have in password
    """
	wordfile = xp.locate_wordfile()
	mywords = xp.generate_wordlist(wordfile=wordfile, min_length=5, max_length=8)
	return xp.generate_xkcdpassword(mywords, delimiter="-", numwords=length)


def _hash_passwd(password):
	"""
    Hash the provided string using SHA512-Crypt

    Keyword arguments:
    password -- Key to hash
    """
	pwhash = sha512.hash(password)
	return "{SHA512-CRYPT}" + pwhash


def set_app_passwd(username):
	"""
    Generate a random password, hash and store it, then return the original 
    password.

    Keyword arguments:
    username -- User who will be assigned the new password
    """
	has_passwd = AppSpecificPassword.query.filter_by(user = username).first()
	if has_passwd:
		raise OTPAlreadyConfigured

	password = _generate_passwd()
	hashed = _hash_passwd(password)

	app_passwd = AppSpecificPassword(user=username, password=hashed)
	db.session.add(app_passwd)
	db.session.commit()

	return password


def delete_app_passwd(username):
	AppSpecificPassword.query.filter_by(user = username).delete()
	db.session.commit()



