"""
Functions for interacting with the Keycloak service.
"""

import json
import logging

from keycloak import KeycloakAdmin, KeycloakOpenID
import requests
import pyotp

from selfservice import app

LOG = logging.getLogger(__name__)

DEVICE_NAME = "SelfService"

class OTPInvalidCode(Exception):
    """
    Error when the initial code does not match expected. 
    """
    pass

class OTPNotConfigured(Exception):
    """
    Error for accounts who don't have OTP configured.
    """

    pass

class OTPAlreadyConfigured(Exception):
    """
    Error for accounts who already have OTP configured.
    """

    pass


class OTPConfigError(Exception):
    """
    Error when unable to properly configure OTP.
    """

    pass


def generate_otp(secret):
    """
    Get current OTP for given secret.
    """
    totp = pyotp.TOTP(secret)
    code = totp.now()
    return code


def get_kc_user_id(username):
    """
    Login as Keycloak Admin and Impersonate User

    Keyword arguments:
    username -- Username of account to generate secret for
    """
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
    return user_id

def get_kc_service_account_token():
    """
    Get an auth token for the OIDC client's associated service account
    """

    keycloak_openid = KeycloakOpenID(
        server_url="https://sso.csh.rit.edu/auth/",
        realm_name="csh",
        client_id=app.config["OIDC_CLIENT_CONFIG"]["client_id"],
        client_secret_key=app.config["OIDC_CLIENT_CONFIG"]["client_secret"],
        verify=True
    )
    token = keycloak_openid.token(grant_type="client_credentials")
    return token["access_token"]

def get_kc_otp_is_registered(username):
    user_id = get_kc_user_id(username)
    token = get_kc_service_account_token()
    response = requests.get(
        f"{app.config["OIDC_ISSUER"]}/totp-api/{user_id}/isRegistered/{DEVICE_NAME}",
        headers={"Authorization": f"Bearer {token}"}
    )
    return response.ok


def generate_kc_otp(username):
    """
    Use session to generate a OTP Secret

    Keyword arguments:
    username -- Username of account to generate secret for
    """

    user_id = get_kc_user_id(username)
    token = get_kc_service_account_token()
    response = requests.get(
        f"{app.config["OIDC_ISSUER"]}/totp-api/{user_id}/generate",
        headers={"Authorization": f"Bearer {token}"}
    )
    response.raise_for_status()
    return response.json()['encodedSecret']


def register_kc_otp(username, secret, otp_code):
    """
    Confirm the key given by the user.

    Keyword arguments:
    session -- Session object with Keycloak cookies
    form_data -- Form validation information
    """
    user_id = get_kc_user_id(username)
    token = get_kc_service_account_token()

    response = requests.post(
        f"{app.config["OIDC_ISSUER"]}/totp-api/{user_id}/register",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        json={
            "encodedSecret": secret,
            "initialCode": otp_code,
            "deviceName": DEVICE_NAME,
            "overwrite": False
        }
    )
    resp = response.json()

    if "message" in resp:
        match resp["message"]:
            case "Invalid initial TOTP code":
                raise OTPInvalidCode()
            case "TOTP credential already exists":
                raise OTPAlreadyConfigured()
            case "Invalid secret":
                raise OTPConfigError()
            case "Invalid request":
                raise OTPConfigError()

    if not response.ok:
        app.logger.error(response.text)
        response.raise_for_status()

def delete_kc_otp(username):
    """
    Remove two-factor information from Keycloak account

    Keyword arguments:
    username -- Username of account to manipulate
    """
    user_id = get_kc_user_id(username)
    token = get_kc_service_account_token()

    response = requests.post(
        f"{app.config["OIDC_ISSUER"]}/totp-api/{user_id}/unregister",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        json={
            "deviceName": DEVICE_NAME,
        }
    )
    resp = response.json()

    if "message" in resp:
        match resp["message"]:
            case "TOTP credential not found":
                raise OTPNotConfigured()
            case "Invalid request":
                raise OTPConfigError()

    if not response.ok:
        app.logger.error(response.text)
        response.raise_for_status()
