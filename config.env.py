import os

# Flask config
DEBUG=False
IP=os.environ.get('IP', '0.0.0.0')
PORT=os.environ.get('PORT', '8080')
SERVER_NAME = os.environ.get('SERVER_NAME', 'localhost:8080')
SECRET_KEY = os.environ.get('SECRET_KEY', '[secret]')

# LDAP config
LDAP_BIND_DN=os.environ.get('LDAP_BIND_DN', 'krbprincipalname=null,cn=services,cn=accounts,dc=csh,dc=rit,dc=edu')
LDAP_BIND_PW=os.environ.get('LDAP_BIND_PW', '')

# OpenID Connect SSO config
OIDC_ISSUER = os.environ.get('OIDC_ISSUER', 'https://sso.csh.rit.edu/auth/realms/csh')
OIDC_CLIENT_CONFIG = {
    'client_id': os.environ.get('OIDC_CLIENT_ID', 'selfservice'),
    'client_secret': os.environ.get('OIDC_CLIENT_SECRET', ''),
    'post_logout_redirect_uris': [os.environ.get('OIDC_LOGOUT_REDIRECT_URI',
                                                 'https://account.csh.rit.edu/logout')]
}
SQLALCHEMY_DATABASE_URI = os.environ.get(
    'DATABASE_URI',
    'sqlite:///{}'.format(os.path.join(os.getcwd(), 'data.db')))
SQLALCHEMY_TRACK_MODIFICATIONS = False

RECAPTCHA_ENABLED = True
RECAPTCHA_SITE_KEY = os.environ.get('RECAPTCHA_SITE_KEY', '')
RECAPTCHA_SECRET_KEY = os.environ.get('RECAPTCHA_SECRET_KEY', '')
RECAPTCHA_THEME = "light"
RECAPTCHA_TYPE = "image"
RECAPTCHA_SIZE = "normal"
