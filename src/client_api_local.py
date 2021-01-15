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
			if item.is_enabled:
				self.logger.debug('{:s} hwid ({:s}) found is_enabled = ({:s}).'.format(self.log_name, hwid_str, str(item.is_enabled)))
				return(True)
			else:	
				self.logger.debug('{:s} hwid ({:s}) found is_enabled = ({:s}).'.format(self.log_name, hwid_str, str(item.is_enabled)))
				return(False)
