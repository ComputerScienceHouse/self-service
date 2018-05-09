from selfservice import app
from csh_ldap import CSHLDAP

import re

def verif_methods(username):

	methods = {
		"emails": [],
		"phones": [],
		"rituid": None
	}

	conn = CSHLDAP(app.config['LDAP_BIND_DN'], app.config['LDAP_BIND_PW'])
	user = conn.get_member("ac610790-0237-11e8-b62e-76e40d50b972")

	if user.mail:
		for addr in user.__getattr__("mail", as_list=True):
			if "csh.rit.edu" not in addr:
				name, domain = addr.split("@")
				display = name[:1] + "..." + name[-1:] + "@" + domain
				methods["emails"].append({"data": addr, "display": display})

	if user.mobile:
		for number in user.__getattr__("mobile", as_list=True):
			stripped = re.sub("[^0-9]", "", number)
			if len(stripped) == 10:
				display = "(XXX) XXX-{}".format(stripped[-4:])
				methods["phones"].append({"data": stripped, "display": display})

	if user.telephoneNumber:
		for number in user.__getattr__("telephoneNumber", as_list=True):
			stripped = re.sub("[^0-9]", "", number)
			if len(stripped) == 10:
				methods["phones"].append(stripped)

	if user.ritDn:
		methods['rituid'] = user.ritDn.split(",")[0].replace("uid=", "")

	return methods
