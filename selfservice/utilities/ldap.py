from python_freeipa.exceptions import NotFound
from selfservice import app, ldap, ipa
from ldap import SCOPE_SUBTREE
import json
import uuid
import re


def verif_methods(username):

    methods = {"email": [], "phone": [], "rit": None}

    user = ldap.get_member(username, True)

    if user.mail:
        for addr in user.__getattr__("mail", as_list=True):
            if "rit.edu" not in addr:
                name, domain = addr.split("@")
                display = name[:1] + "..." + name[-1:] + "@" + domain
                methods["email"].append({"data": addr, "display": display})

    if user.mobile:
        for number in user.__getattr__("mobile", as_list=True):
            stripped = re.sub("[^0-9]", "", number)
            if len(stripped) == 10:
                display = "(XXX) XXX-{}".format(stripped[-4:])
                methods["phone"].append({"data": stripped, "display": display})

    if user.telephoneNumber:
        for number in user.__getattr__("telephoneNumber", as_list=True):
            stripped = re.sub("[^0-9]", "", number)
            if len(stripped) == 10:
                methods["phone"].append(stripped)

    if user.ritDn:
        methods["rit"] = user.ritDn.split(",")[0].replace("uid=", "")

    return methods


def get_members():
    members = []
    ldap_conn = ldap.get_con()
    res = ldap_conn.search_s(
        "cn=users,cn=accounts,dc=csh,dc=rit,dc=edu",
        SCOPE_SUBTREE,
        "(uid=*)",
        ["uid", "displayName"],
    )
    for member in res:
        members.append(
            {
                "value": member[1]["uid"][0].decode("utf-8"),
                "display": member[1]
                .get("displayName", member[1]["uid"])[0]
                .decode("utf-8"),
            }
        )

    return members


def ipa_login():
    username = app.config["LDAP_BIND_DN"].split(",")[0].split("=")[1]
    password = app.config["LDAP_BIND_PW"]
    ipa.login(username, password)


def create_ipa_otp(username, secret):
    ipa_login()
    data = {"ipatokenowner": username, "ipatokenotpkey": secret}
    ipa._request("otptoken_add", params=data)


def delete_ipa_otp(username):
    ipa_login()
    tokens = []
    token_info = ipa._request("otptoken_find", params={"ipatokenowner": username})
    for token in token_info["result"]:
        ipa._request("otptoken_del", args=[token["ipatokenuniqueid"][0]])
