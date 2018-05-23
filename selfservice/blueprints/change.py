from flask import Blueprint, render_template, request, redirect, flash
from selfservice.utilities.reset import passwd_change, PasswordChangeFailed
from selfservice import version

change_bp = Blueprint('change', __name__)

@change_bp.route('/change', methods=['GET', 'POST'])
def change():
	if request.method == "GET":
		return render_template("reset.html",
			version = version,
			changing = True)

	username = request.form.get("username")
	old_pw = request.form.get("current")
	new_pw = request.form.get("password")
	verify = request.form.get("verify")

	if new_pw == verify:
		if len(new_pw) >= 12:
			try:
				passwd_change(
					username,
					old_pw,
					new_pw)
				return render_template('success.html',
					reset=True,
    				version = version)
			except PasswordChangeFailed:
				flash("Incorrect password, please try again.")
		else:
			flash("Your password does not meet the requirements below.")
	else:
		flash("Whoops, those passwords didn't match!")

	return redirect("/change")
