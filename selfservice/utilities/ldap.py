from selfservice import app, ldap
import re

def verif_methods(username):

	methods = {
		"email": [],
		"phone": [],
		"rit": None
	}

	
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
		methods['rit'] = user.ritDn.split(",")[0].replace("uid=", "")

	return methods

