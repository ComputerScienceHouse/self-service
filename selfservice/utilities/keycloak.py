from bs4 import BeautifulSoup
from keycloak import KeycloakAdmin
from selfservice import app
import requests
import pyotp
import json


class OTPAlreadyConfigured(Exception):
    pass


class OTPConfigError(Exception):
    pass


def generate_otp(secret):
    totp = pyotp.TOTP(secret)
    code = totp.now()
    return code


def get_kc_cookies(username):
    # Login as Keycloak Admin and Impersonate User
    admin = KeycloakAdmin(
        server_url="https://sso.csh.rit.edu/auth/",
        username=app.config["KC_ADMIN_USER"],
        password=app.config["KC_ADMIN_PW"],
        realm_name="master",
        verify=True,
    )
    conn = admin.connection
    user = conn.raw_get(
        "admin/realms/csh/users?first=0&max=20&search={}@csh.rit.edu".format(username)
    )
    user_id = json.loads(user.text)[0]["id"]
    imp = conn.raw_post(
        "admin/realms/csh/users/{}/impersonation".format(user_id),
        data=json.dumps({"user": user_id, "realm": "csh"}),
    )
    return imp.cookies


def create_kc_otp(username):
    # Use session to generate a OTP Secret
    session = requests.Session()
    session.cookies = get_kc_cookies(username)
    page = session.get(
        "https://sso.csh.rit.edu/auth/realms/csh/account/totp?mode=manual"
    )

    # Check if the user already has OTP configured
    if "Configured Authenticators" in page.text:
        raise OTPAlreadyConfigured

    soup = BeautifulSoup(page.text, "html.parser")
    key = soup.find("span", {"id": "kc-totp-secret-key"})
    parsed_key = key.text.replace(" ", "")
    state_checker = soup.find("input", {"id": "stateChecker"}).get("value")
    secret = soup.find("input", {"id": "totpSecret"}).get("value")
    form_data = {
        "stateChecker": state_checker,
        "totp": generate_otp(parsed_key),
        "totpSecret": secret,
        "submitAction": "Save",
    }
    return (session, form_data, parsed_key)


def confirm_kc_otp(session, form_data, parsed_key):
    # Confirm the key.
    save = session.post(
        "https://sso.csh.rit.edu/auth/realms/csh/account/totp", data=form_data
    )

    if "Configured Authenticators" not in save.text:
        raise OTPConfigError


def delete_kc_otp(username):
    session = requests.Session()
    session.cookies = get_kc_cookies(username)
    page = session.get(
        "https://sso.csh.rit.edu/auth/realms/csh/account/totp?mode=manual"
    )
    soup = BeautifulSoup(page.text, "html.parser")
    state_checker = soup.find("input", {"id": "stateChecker"}).get("value")
    form_data = {"stateChecker": state_checker, "submitAction": "Delete"}
    delete = session.post(
        "https://sso.csh.rit.edu/auth/realms/csh/account/totp", data=form_data
    )
    check = session.get(
        "https://sso.csh.rit.edu/auth/realms/csh/account/totp?mode=manual"
    )

    if "Configured Authenticators" in check.text:
        raise OTPConfigError
