"""
Flask blueprint for handling creating and removing OTP secrets from accounts.
"""

import logging

import pyotp
from flask import Blueprint, render_template, request, redirect, flash
from flask import session as flask_session

from selfservice import version, auth, OIDC_PROVIDER
from selfservice.utilities.app_passwd import delete_app_passwd
from selfservice.utilities.keycloak import (
    OTPConfigError,
    OTPInvalidCode,
    OTPAlreadyConfigured,
    get_kc_otp_is_registered,
    generate_kc_otp,
    register_kc_otp,
    delete_kc_otp,
)
from selfservice.utilities.ldap import delete_ipa_otp

otp_bp = Blueprint("otp", __name__)

LOG = logging.getLogger(__name__)


@otp_bp.route("/otp", methods=["GET", "POST"])
@auth.oidc_auth(OIDC_PROVIDER)
def enable():
    """
    Creates a Keycloak OTP secret and then displays that to the user.
    """
    username = flask_session["userinfo"].get("preferred_username")
    secret = request.args.get("secret", default="", type=str)
    otp_code = request.form.get("otp-code", default="")

    if request.method == "GET":
        kc_registered = get_kc_otp_is_registered(username)

        # If already registered
        if kc_registered:
            return render_template("otp.html", version=version, configured=True)

        secret = generate_kc_otp(username)
        otp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            f"{username}@csh.rit.edu", issuer_name="CSH"
        )

        return render_template(
            "otp.html", version=version, otp_uri=otp_uri, secret=secret
        )

    otp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
        f"{username}@csh.rit.edu", issuer_name="CSH"
    )
    if not secret:
        flash("Invalid secret provided. Please try again.")
        return redirect("/otp")
    if not otp_code:
        flash(
            "One time password provided did not match expected value. "
            "Please scan the code and try again."
        )
        return render_template(
            "otp.html", version=version, otp_uri=otp_uri, secret=secret
        )

    try:
        register_kc_otp(username, secret, otp_code)
    except OTPInvalidCode:
        flash(
            "One time password provided did not match expected value."
            "Please scan the code and try again."
        )
        return render_template(
            "otp.html", version=version, otp_uri=otp_uri, secret=secret
        )
    except OTPConfigError:
        flash("Invalid secret, try again.")
        return redirect("/otp")
    except OTPAlreadyConfigured:
        flash("2FA already configured.")
        return redirect("/otp")

    return render_template(
        "otp.html", version=version, configured=True
    )


@otp_bp.route("/otp/remove", methods=["GET"])
@auth.oidc_auth(OIDC_PROVIDER)
def disable():
    """
    Removes any tokens from both Keycloak and FreeIPA
    """

    username = flask_session["userinfo"].get("preferred_username")

    try:
        delete_kc_otp(username)
        delete_ipa_otp(username)
        delete_app_passwd(username)
    except OTPConfigError:
        flash("Error removing two-factor! Please contact and RTP.")
        LOG.exception("Failed to remove OTP for %s", username)
        return redirect("/otp")

    return redirect("/otp")
