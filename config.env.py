import os

# Flask config
DEBUG = False
IP = os.environ.get("IP", "0.0.0.0")
PORT = os.environ.get("PORT", "8080")
SERVER_NAME = os.environ.get("SERVER_NAME", "localhost:8080")
SECRET_KEY = os.environ.get("SECRET_KEY", "[secret]")

# LDAP config
LDAP_BIND_DN = os.environ.get(
    "LDAP_BIND_DN", "krbprincipalname=null,cn=services,cn=accounts,dc=csh,dc=rit,dc=edu"
)
LDAP_BIND_PW = os.environ.get("LDAP_BIND_PW", "")

# Sentry config
# Do not set the DSN for local development
SENTRY_DSN = os.environ.get("SENTRY_DSN", "")

# OpenID Connect SSO config
OIDC_ISSUER = os.environ.get("OIDC_ISSUER", "https://sso.csh.rit.edu/auth/realms/csh")
OIDC_CLIENT_CONFIG = {
    "client_id": os.environ.get("OIDC_CLIENT_ID", "selfservice"),
    "client_secret": os.environ.get("OIDC_CLIENT_SECRET", ""),
    "post_logout_redirect_uris": [
        os.environ.get("OIDC_LOGOUT_REDIRECT_URI", "https://account.csh.rit.edu/logout")
    ],
}
KC_ADMIN_USER = os.environ.get("KC_ADMIN_USER", "selfservice")
KC_ADMIN_PW = os.environ.get("KC_ADMIN_PW", "")

SQLALCHEMY_DATABASE_URI = os.environ.get(
    "DATABASE_URI",
    "postgresql://selfservice:supersecretpassword@localhost:5433/selfservice"
)
SQLALCHEMY_TRACK_MODIFICATIONS = False

XCAPTCHA_ENABLED = True
XCAPTCHA_SITE_KEY = os.environ.get("XCAPTCHA_SITE_KEY", "")
XCAPTCHA_SECRET_KEY = os.environ.get("XCAPTCHA_SECRET_KEY", "")
XCAPTCHA_THEME = "light"
XCAPTCHA_TYPE = "image"
XCAPTCHA_SIZE = "normal"

TWILIO_SID = os.environ.get("TWILIO_SID", "")
TWILIO_TOKEN = os.environ.get("TWILIO_TOKEN", "")
TWILIO_NUMBER = os.environ.get("TWILIO_NUMBER", "")
TWILIO_SERVICE_SID = os.environ.get("TWILIO_SERVICE_SID", "")
