from datetime import datetime, timedelta

def is_expired(timestamp, minutes):
	exptime = datetime.utcnow() - timedelta(minutes=minutes)
	expired = bool(timestamp < exptime)
	return(expired)
