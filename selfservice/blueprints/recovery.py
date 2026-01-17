"""
Flask blueprint for handling identity verification and account recovery.
"""

import uuid
import logging

from flask import Blueprint, render_template, request, redirect, flash
from flask import session as flask_session

from selfservice.utilities.general import is_expired, email_recovery, phone_recovery
from selfservice.utilities.reset import (
    generate_token,
    generate_pin,
    passwd_reset,
    TokenAlreadyExists,
)
from selfservice.utilities.ldap import verif_methods, get_members

from selfservice.models import RecoverySession, PhoneVerification, ResetToken
from selfservice import db, auth, xcaptcha, ldap, version, OIDC_PROVIDER

LOG = logging.getLogger(__name__)

recovery_bp = Blueprint("recovery", __name__)


@recovery_bp.route("/recovery", methods=["GET", "POST"])
def create_session():
    """
    Renders the password recovery form, handles the creation of a recovery
    session, and redirect the user to their session.
    """

    if request.method == "GET":
        return render_template("recovery.html", version=version)

    if xcaptcha.verify():

        # If we can't find an account, flash error.
        try:
            member = ldap.get_member(request.form["username"], True)
        except KeyError:
            flash(
                "Uh oh, either that account doesn't exist or we don't have "
                + "a way to verify your identity. Make sure you entered the "
                + "correct username or contact an RTP (rtp@csh.rit.edu)."
            )
            return redirect("/recovery")

        rtp_dn = "cn=rtp,cn=groups,cn=accounts,dc=csh,dc=rit,dc=edu"
        if rtp_dn in member.groups():
            flash(
                "For security reasons, RTPs cannot use this form. Please "
                + "email rtp@csh.rit.edu for further assistance."
            )
            return redirect("/recovery")

        failed_dn = "cn=failed,cn=groups,cn=accounts,dc=csh,dc=rit,dc=edu"
        if failed_dn in member.groups():
            flash(
                "According to our records you failed a freshman evaluation "
                + "and lost access to your account. If this is incorrect, "
                + "please contact rtp@csh.rit.edu."
            )
            return redirect("/recovery")

        # Generate a random UUID for session object.
        session_id = str(uuid.uuid4())

        # Create the object in the database.
        session = RecoverySession(id=session_id, username=request.form["username"])
        db.session.add(session)
        db.session.commit()

        # Redirect the user to thier session.
        return redirect("/recovery/" + session_id)
    flash("Please complete the reCaptcha.")
    return redirect("/recovery")


@recovery_bp.route("/recovery/<recovery_id>")
def verify_identity(recovery_id):
    """
    Renders the identity verification options for the user.
    """

    # Retrieve the session object.
    session = RecoverySession.query.filter_by(id=recovery_id).first()
    methods = verif_methods(session.username)

    # Make sure it isn't expired.
    if is_expired(session.created, 10):
        flash("Sorry, your session has expired.")
        return redirect("/recovery")

        # Make sure that methods are valid
    possible_methods = 0
    for _, value in methods.items():
        if value:
            possible_methods += 1

    if possible_methods == 0:
        flash(
            "We weren't able to find any information attached to your account "
            + "which could be used to automatically recover it. Please email "
            + "rtp@csh.rit.edu for further assistance."
        )
        return redirect("/recovery")

    return render_template(
        "options.html",
        username=session.username,
        recovery_id=recovery_id,
        methods=methods,
        version=version,
    )


@recovery_bp.route("/recovery/<recovery_id>/<method>")
def method_selection(recovery_id, method):
    """
    Depending on the selection made by the users, dispatch ID verification
    message.
    """

    # Parse expected URL paramters.
    index = request.args.get("index", default=0, type=int)

    # Retrieve the session object.
    session = RecoverySession.query.filter_by(id=recovery_id).first()
    methods = verif_methods(session.username)

    # Make sure it isn't expired.
    if is_expired(session.created, 10):
        flash("Sorry, your session has expired.")
        return redirect("/recovery")

        # Get Method
    if method == "email":
        # Generate a random UUID for reset token.
        try:
            token = generate_token(session)
        except TokenAlreadyExists:
            flash(
                "This session has already been used to generate an "
                + "email recovery token. Please wait for the session to "
                + "expire and try again or contact an RTP."
            )
            return redirect("/recovery")

        rec_email = methods["email"][index]["data"]

        try:
            email_recovery(username=session.username, address=rec_email, token=token)
            return render_template("success.html", version=version)
        except:
            flash("Uh oh, something went wrong. Please try again later.")
            return redirect("/recovery")

    elif method == "phone":
        try:
            token = generate_pin(session)
        except TokenAlreadyExists:
            flash(
                "This session has already been used to generate a "
                + "phone recovery token. Please wait for the session to "
                + "expire and try again or contact an RTP."
            )
            return redirect("/recovery")

        try:
            phone_recovery(phone=methods["phone"][index]["data"], token=token)
            return render_template(
                "phone.html",
                recovery_id=session.id,
                username=session.username,
                version=version,
            )
        except:
            LOG.exception("Failed to send SMS to phone number!")
            flash("Uh oh, something went wrong. Please try again later.")
            return redirect("/recovery")


@recovery_bp.route("/recovery/<recovery_id>/phone/verify", methods=["POST"])
def verify_phone(recovery_id):
    """
    Check the provided verification code against our stored code.
    """
    session = RecoverySession.query.filter_by(id=recovery_id).first()
    token = PhoneVerification.query.filter_by(session=recovery_id).first()

    if request.form["verify"] == token.code:
        token = ResetToken.query.filter_by(session=recovery_id).first()
        if not token:
            token = generate_token(session)
        return redirect("/reset?token=" + token)
    flash("Your verification code did not match, sorry!")
    return redirect("/recovery")


@recovery_bp.route("/reset", methods=["GET", "POST"])
def reset_password():
    """
    Renders the password reset page and forwards requests to FreeIPA.
    """

    token = request.args.get("token", default="", type=str)

    token_data = ResetToken.query.filter_by(token=token).first()

    # Redirect if the token provided isn't valid.
    if (
        not token
        or not token_data
        or is_expired(token_data.created, 30)
        or token_data.used
    ):
        flash(
            "Oops! Invalid or expired reset token. Each token is only "
            + "valid for 30 minutes after it is issued."
        )
        return redirect("/recovery")

        # Display the reset page.
    if request.method == "GET":
        return render_template("reset.html", token=token_data.token, version=version)

        # Lets actually do the reset.
    if request.form["password"] == request.form["verify"]:
        if len(request.form["password"]) >= 12:
            passwd_reset(
                username=token_data.username, password=request.form["password"]
            )
            try:
                passwd_reset(
                    username=token_data.username, password=request.form["password"]
                )
                token_data.used = True
                db.session.commit()
                return render_template("success.html", reset=True, version=version)
            except:
                flash("LDAP Error Occurred... Please contact an RTP.")
        else:
            flash("Your password does not meet the requirements below.")
    else:
        flash("Whoops, those passwords didn't match!")

    return redirect(f"/reset?token={token}")


@recovery_bp.route("/admin", methods=["GET", "POST"])
@auth.oidc_auth(OIDC_PROVIDER)
def admin():
    """
    Allow RTPs to create reset tokens for accounts.
    """
    if "/admins/rtp" not in flask_session["userinfo"].get("groups"):
        flash("Nice try. 😉 ")
        return redirect("/recovery")

    if request.method == "GET":
        token = None
    else:
        # Generate a random UUID for session object.
        session_id = str(uuid.uuid4())

        # Create the object in the database.
        session_data = RecoverySession(id=session_id, username=request.form["username"])
        db.session.add(session_data)
        db.session.commit()

        token = generate_token(session_data)

    members = get_members()
    uid = str(flask_session["userinfo"].get("preferred_username", ""))
    last_sessions = [
        {
            "username": s.username,
            "session_created": s.session_created,
            "session_expired": (
                (is_expired(s.session_created, 10) and not s.token_created)
                or is_expired(s.token_created, 30)
            ),
            "token_created": s.token_created,
            "used": s.used,
        }
        for s in RecoverySession.query.outerjoin(
            ResetToken, RecoverySession.id == ResetToken.session
        )
        .with_entities(
            RecoverySession.username,
            RecoverySession.created.label("session_created"),
            ResetToken.created.label("token_created"),
            ResetToken.used,
        )
        .order_by(RecoverySession.created.desc())
        .limit(20)
        .all()
    ]

    return render_template(
        "admin.html",
        version=version,
        members=members,
        username=uid,
        sessions=last_sessions,
        token=token,
    )
