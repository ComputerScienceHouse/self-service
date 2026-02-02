"""
Flask blueprint for handling all password changes for users who know their
current password.
"""

from flask import Blueprint, render_template, request, redirect, flash
from selfservice.utilities.reset import passwd_change, PasswordChangeFailed, PasswordPolicyViolation, \
    CurrentPasswordInvalid
from selfservice import version

change_bp = Blueprint("change", __name__)


@change_bp.route("/change", methods=["GET", "POST"])
def change():
    """
    Renders the change password page and passes requests to FreeIPA.
    """
    if request.method == "GET":
        return render_template("reset.html", version=version, changing=True)

    username = request.form.get("username")
    old_pw = request.form.get("current")
    new_pw = request.form.get("password")
    verify = request.form.get("verify")

    if new_pw == verify:
        try:
            passwd_change(username, old_pw, new_pw)
            return render_template("success.html", reset=True, version=version)
        except CurrentPasswordInvalid:
            flash("Your current password is incorrect, please try again.")
        except PasswordPolicyViolation as e:
            flash("Your new password does not match the requirements:", e.message)
        except PasswordChangeFailed:
            flash("An unknown error occurred.")
    else:
        flash("Whoops, those passwords didn't match!")

    return redirect("/change")
