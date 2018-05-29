"""
SQLAlchemy Database Models
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    DateTime,
    Boolean,
    Binary,
    func,
)
from selfservice import db


class ResetToken(db.Model):
    """
    Reset tokens are generated once an identity has been verified. They allow
    the user access to the reset page.
    """
    __tablename__ = "token"
    id = Column(Integer, primary_key=True)
    username = Column(String(64), nullable=False)
    created = Column(DateTime, default=func.current_timestamp())
    token = Column(String(36))
    session = Column(String(36), ForeignKey("session.id"))
    used = Column(Boolean)


class RecoverySession(db.Model):
    """
    A recovery session is created once a user enters their username and
    completes the reCaptcha. It is used to track Reset Tokens and Phone
    Verification numbers per session.
    """
    __tablename__ = "session"
    id = Column(String(36), primary_key=True)
    username = Column(String(64), nullable=False)
    created = Column(DateTime, default=func.current_timestamp())


class PhoneVerification(db.Model):
    """
    Phone Verification codes will be sent to the user and then asked for
    in order to verify a phone number.
    """
    __tablename__ = "phone_codes"
    code = Column(String(6), primary_key=True)
    session = Column(String(36), ForeignKey("session.id"))


class OTPSession(db.Model):
    """
    Once an OTP secret has been generated for a user, we pickle their session
    so that we can retrieve it and eventually verify their token.
    """
    __tablename__ = "otp_session"
    secret = Column(String(100), primary_key=True)
    form = Column(Binary)
    session = Column(Binary)
