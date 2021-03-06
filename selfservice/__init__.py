"""
Self-Service Account Management Utility
Computer Science House
Rochester Institute of Technology

Author: Marc Billow
"""

import os
import subprocess
import srvlookup
from csh_ldap import CSHLDAP
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_pyoidc.flask_pyoidc import OIDCAuthentication
from flask_pyoidc.provider_configuration import ProviderConfiguration, ClientMetadata
from flask_recaptcha import ReCaptcha
from flask_sqlalchemy import SQLAlchemy
from python_freeipa import Client
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_migrate import Migrate
from flask_qrcode import QRcode

import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration


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

# Setup Sentry tracking
sentry_sdk.init(
    dsn=app.config["SENTRY_DSN"],
    integrations=[FlaskIntegration(), SqlalchemyIntegration()],
)

# Create the database session.
db = SQLAlchemy(app)
from selfservice.models import *  # pylint: disable=wrong-import-position

migrate = Migrate(app, db)

# Create recaptcha object
recaptcha = ReCaptcha()
recaptcha.init_app(app)

# OIDC Initialization
OIDC_PROVIDER = "csh"
client_info = ClientMetadata(**app.config["OIDC_CLIENT_CONFIG"])
provider = ProviderConfiguration(
    issuer=app.config["OIDC_ISSUER"], client_metadata=client_info
)
auth = OIDCAuthentication(app=app, provider_configurations={OIDC_PROVIDER: provider})

# Connect to LDAP
ldap = CSHLDAP(app.config["LDAP_BIND_DN"], app.config["LDAP_BIND_PW"])

# Find FreeIPA server
ldap_srvs = srvlookup.lookup("ldap", "tcp", "csh.rit.edu")
ldap_uri = ldap_srvs[0].hostname

# FreeIPA API Connection
ipa = Client(ldap_uri, version="2.215")

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
    """
    Renders an error page.
    """
    return render_template("error.html", e=e), 500


@app.route("/")
def index():
    """
    Renders the initial landing page.
    """
    return render_template("index.html", version=version)


@app.route("/health")
@limiter.exempt
def health():
    """
    Shows an ok status if the application is up and running
    """
    return {"status": "ok"}
