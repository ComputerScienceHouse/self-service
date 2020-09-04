"""
Functions relating to the verification of users and subsequent account resets.
"""

import random
import uuid
import requests
import ldap
import srvlookup

from selfservice.models import ResetToken, PhoneVerification
from selfservice.utilities.general import is_expired
from selfservice import db, app


class TokenAlreadyExists(Exception):
    """
    Error generated when user had already used their session to generate
    a reset token.
    """

    pass


class PasswordChangeFailed(Exception):
    """
    Error raised when a failure occured during the reset process.
    """

    pass


def generate_token(session):
    """
    Create a password reset token.

    Keyword arguments:
    session -- Instance of RecoverySession model
    """
    # Generate a random UUID for reset token.
    token = str(uuid.uuid4())

    # Verify that this session creates only one token.
    previous = ResetToken.query.filter_by(session=session.id).first()
    if previous:
        raise TokenAlreadyExists()

        # Create the object in the database.
    reset = ResetToken(
        username=session.username, token=token, session=session.id, used=False
    )
    db.session.add(reset)
    db.session.commit()

    return token


def generate_pin(session):
    """
    Generate a six-digit pin for SMS verification.

    Keyword arguments:
    session -- Instance of RecoverySession model
    """

    # Generate a random UUID for reset token.
    token = f"{random.randrange(1, 10**6):06}"

    # Verify that this session creates only one token.
    previous = ResetToken.query.filter_by(session=session.id).first()
    if previous:
        raise TokenAlreadyExists()

        # Create the object in the database.
    reset = PhoneVerification(code=token, session=session.id)
    db.session.add(reset)
    db.session.commit()

    return token


def valid_token(token_id):
    """
    Ensure that the token provided is still valid.

    Keyword arguments:
    token_id -- ID of a ResetToken object
    """

    token_data = ResetToken.query.filter_by(token=token_id).first()

    if token_data:
        if is_expired(token_data.created, 30):
            return False
        return True
    else:
        return False


def passwd_reset(username, password):
    """
    Use the password provided by the user to reset their account in FreeIPA
    and then "change" their password to the same thing.

    Keyword arguments:
    username -- Username of the user to reset
    password -- Desired password for the user
    """

    # Create LDAP admin session to perform initial reset.
    dn = "uid={},cn=users,cn=accounts,dc=csh,dc=rit,dc=edu".format(username)

    # Find FreeIPA server
    ldap_srvs = srvlookup.lookup("ldap", "tcp", "csh.rit.edu")
    ldap_uri = ldap_srvs[0].hostname
    l = ldap.initialize("ldaps://{}".format(ldap_uri))
    l.simple_bind_s(app.config["LDAP_BIND_DN"], app.config["LDAP_BIND_PW"])
    l.modify_s(dn, [(ldap.MOD_REPLACE, "userPassword", [password.encode()])])
    l.modify_s(dn, [(ldap.MOD_REPLACE, "nsaccountlock", ["false".encode()])])

    # FreeIPA automatically expires the password set through the previous
    # method, so we need to use their password change API to get past that.
    requests.post(
        "https://{}/ipa/session/change_password".format(ldap_uri),
        data={"user": username, "old_password": password, "new_password": password},
    )


def passwd_change(username, old_pw, new_pw):
    """
    Change a user's password when the previous one is know.

    Keyword arguments:
    username -- Username of the user to alter
    old_pw -- Current password for the account
    new_pw -- Desired new password.
    """
    # Find FreeIPA server
    ldap_srvs = srvlookup.lookup("ldap", "tcp", "csh.rit.edu")
    ldap_uri = ldap_srvs[0].hostname
    change = requests.post(
        "https://{}/ipa/session/change_password".format(ldap_uri),
        data={"user": username, "old_password": old_pw, "new_password": new_pw},
    )
    if change.headers.get("X-IPA-Pwchange-Result") == "invalid-password":
        raise PasswordChangeFailed
