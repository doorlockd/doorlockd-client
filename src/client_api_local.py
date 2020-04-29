from models import Tag, UnknownTag
from libs.base import DoorlockdBaseClass

class ClientApiDoorlockd(DoorlockdBaseClass):
	
	def lookup_detected_hwid(self, hwid_str):
		''' lookup detected hwid, 
			
		'''
		# lookup hwid in db
		item = Tag.where('hwid', hwid_str).first()
		if not item: 
			# hwid not found
			self.logger.debug('{:s} hwid ({:s}) not found, adding to UnkownTag.'.format(self.log_name, hwid_str))
			# UnknownTag.create(hwid=hwid_str)
			ut = UnknownTag.first_or_new(hwid=hwid_str)
			ut.touch()
			ut.save()
			return(False)
		else:
			if not item.is_disabled:
				self.logger.debug('{:s} hwid ({:s}) found is_disabled = ({:s}).'.format(self.log_name, hwid_str, str(item.is_disabled)))
				return(True)
			else:	
				self.logger.debug('{:s} hwid ({:s}) found is_disabled = ({:s}).'.format(self.log_name, hwid_str, str(item.is_disabled)))
				return(False)
