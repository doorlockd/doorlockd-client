from models import Tag, UnknownTag

from libs.data_container import data_container as dc
logger = dc.logger


class RfidAuth:
	
	def has_access(self, hwid_str):
		''' lookup detected hwid, 
			
		'''
		# lookup hwid in db
		item = Tag.where('hwid', hwid_str).first()
		if not item: 
			# hwid not found
			logger.debug('hwid ({:s}) not found, adding to UnkownTag.'.format(hwid_str))
			# UnknownTag.create(hwid=hwid_str)
			ut = UnknownTag.first_or_new(hwid=hwid_str)
			ut.touch()
			ut.save()
			return(False)
		else:
			if item.is_enabled:
				logger.debug('hwid ({:s}) found is_enabled = ({:s}).'.format(hwid_str, str(item.is_enabled)))
				return(True)
			else:	
				logger.debug('hwid ({:s}) found is_enabled = ({:s}).'.format(hwid_str, str(item.is_enabled)))
				return(False)
