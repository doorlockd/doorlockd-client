

def hwid2hexstr(hwid):
	'''	Convert array of integers into a collon seperated hex string.

	hwid as suplied by rdr. 
	hexstr as stored as string in db.
	'''
	return(':'.join("{:02x}".format(p) for p in hwid))
