"""
General helper funtions that reduce copied code.
"""

import smtplib

from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.utils import formatdate
from twilio.rest import Client
from flask import current_app


def is_expired(timestamp, minutes):
    """
    Helper function to quickly check session expiry.
    """

    if not timestamp:
        return None

    exptime = datetime.utcnow() - timedelta(minutes=minutes)
    expired = bool(timestamp < exptime)
    return expired


def email_recovery(username, address, token):
    """
    Send verification emails based on below template.
    """
    message = (
        "Hey there!\n\n\tWe just received a request to reset "
        + "the Computer Science House account '{}'. According the information "
        + "we have about the account, this email ({}) is listed as an "
        + "alternative. If you requested this password reset, please click "
        + "the link below and proceed with the password reset. If not, please "
        + "contact an RTP immediately at rtp@csh.rit.edu. "
        + "\n\nhttps://account.csh.rit.edu/reset?token={}\n\n"
        + "This token is only valid for 30 minutes, after that you will need to "
        + "reverify your identity.\n\n"
        + "Thanks,\nRoot Type People\nComputer Science House\nrtp@csh.rit.edu"
        + "\n\nThis message was automatically generated by the CSH account "
        + "recovery utility."
    )

    message = message.format(username, address, token)

    email = MIMEText(message)
    email["To"] = address
    email["From"] = "CSH Account Recovery <rtp@csh.rit.edu>"
    email["Subject"] = "Your Requested Account Reset"
    email["Date"] = formatdate()

    server = smtplib.SMTP("mail.csh.rit.edu")
    server.send_message(email)
    server.quit()


def phone_recovery(phone, token):
    """
    Use Twilio to send token.
    """
    from_number = current_app.config.get("TWILIO_NUMBER")
    service_sid = current_app.config.get("TWILIO_SERVICE_SID")
    client = Client(
        current_app.config.get("TWILIO_SID"), current_app.config.get("TWILIO_TOKEN")
    )

    body = f"Your CSH account recovery PIN is: {token}"

    client.messages.create(
        to=phone, from_=from_number, body=body, messaging_service_sid=service_sid
    )
