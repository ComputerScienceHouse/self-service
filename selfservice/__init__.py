"""
Self-Service Account Management Utility
Computer Science House
Rochester Institute of Technology

Author: Marc Billow
"""

import os
import subprocess
from csh_ldap import CSHLDAP
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_pyoidc.flask_pyoidc import OIDCAuthentication
from flask_recaptcha import ReCaptcha
from flask_sqlalchemy import SQLAlchemy
from python_freeipa import Client
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_migrate import Migrate
from flask_qrcode import QRcode

app = Flask(__name__)

if os.path.exists(os.path.join(os.getcwd(), "config.py")):
    app.config.from_pyfile(os.path.join(os.getcwd(), "config.py"))
else:
    app.config.from_pyfile(os.path.join(os.getcwd(), "config.env.py"))

# Get Git Revision
version = (
    subprocess.check_output(["git", "rev-parse", "--short", "HEAD"])
    .decode("utf-8")
    .rstrip()
)

# Create the database session.
db = SQLAlchemy(app)
from selfservice.models import *  # pylint: disable=wrong-import-position

migrate = Migrate(app, db)

# Create recaptcha object
recaptcha = ReCaptcha()
recaptcha.init_app(app)

# OIDC Initialization
auth = OIDCAuthentication(
    app,
    issuer=app.config["OIDC_ISSUER"],
    client_registration_info=app.config["OIDC_CLIENT_CONFIG"],
)

# Connect to LDAP
ldap = CSHLDAP(app.config["LDAP_BIND_DN"], app.config["LDAP_BIND_PW"])

# FreeIPA API Connection
ipa = Client("stone.csh.rit.edu", version="2.215")

# Configure rate limiting
if not app.config["DEBUG"]:
    limiter = Limiter(
        app, key_func=get_remote_address, default_limits=["50 per day", "10 per hour"]
    )

# Initialize QR Code Generator
qr = QRcode(app)

# Import blueprints
# pylint: disable=wrong-import-position
from selfservice.blueprints.recovery import recovery_bp
from selfservice.blueprints.change import change_bp
from selfservice.blueprints.otp import otp_bp

# pylint: enable=wrong-import-position

# Register blueprints
app.register_blueprint(recovery_bp)
app.register_blueprint(change_bp)
app.register_blueprint(otp_bp)

# Flask Routes


@app.errorhandler(500)
def app_error(e):
    return render_template("error.html"), 500


@app.route("/")
def index():
    """
    Renders the initial landing page.
    """
    return render_template("index.html", version=version)
