from flask import Blueprint, render_template, request, redirect, flash
from flask import session as flask_session

from selfservice.utilities.keycloak import OTPConfigError, generate_otp, \
										   create_kc_otp, confirm_kc_otp, \
										   OTPAlreadyConfigured, delete_kc_otp
from selfservice.utilities.ldap import create_ipa_otp, delete_ipa_otp
from selfservice.models import OTPSession
from selfservice import version, auth, db

import dill as pickle
import pyotp

otp_bp = Blueprint('otp', __name__)

@otp_bp.route('/otp', methods=['GET', 'POST'])
@auth.oidc_auth
def enable():
	username = flask_session["userinfo"].get('preferred_username')
	secret = request.args.get('secret', default = "", type = str)
	otp_code = request.form.get('otp-code', default = "")

	if request.method == "GET":
		try:
			session, form_data, secret = create_kc_otp(username)

			save_session = OTPSession(
				secret = secret,
				form = pickle.dumps(form_data),
				session = pickle.dumps(session))
			db.session.add(save_session)
			db.session.commit()
		except OTPAlreadyConfigured:
			return render_template("otp.html",
				version = version,
				configured = True)

		otp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
			"{}@csh.rit.edu".format(username),
			issuer_name="CSH")

		return render_template("otp.html",
			version = version,
			otp_uri = otp_uri,
			secret = secret)

	otp_session = OTPSession.query.filter_by(secret=secret).first()

	if not secret or not otp_session:
		flash("Invalid secret provided. Please try again.")
		return redirect("/otp")
	elif not otp_code:
		flash("No one time password provided. Please scan the code and try again.")
		return redirect("/otp".format(secret))

	session = pickle.loads(otp_session.session)
	form = pickle.loads(otp_session.form)

	try:
		confirm_kc_otp(session, form, secret)
	except OTPConfigError:
		flash("Invalid one time code provided or session expired.")
		return redirect("/otp".format(secret))

	create_ipa_otp(username, secret)
	return render_template("otp.html",
		version = version,
		configured = True)


@otp_bp.route('/otp/remove', methods=['GET'])
@auth.oidc_auth
def disable():
	username = flask_session["userinfo"].get('preferred_username')

	try:
		delete_kc_otp(username)
		delete_ipa_otp(username)
	except OTPConfigError:
		flash("Error removing two-factor! Please contact and RTP.")
		return redirect("/otp")

	return redirect("/otp")
