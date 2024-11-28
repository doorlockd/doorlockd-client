from libs.data_container import data_container as dc

# import logging
# logger = logging.getLogger(__name__)
logger = dc.logger


class SimpleRfidAuth:
    """rfid_auth using a plain list of hardware ids"""

    def __init__(self, config={}):

        # init BackendApi with config:
        #
        # [module.rfid_auth]
        # type = "SimpleRfidAuth"
        # access_list = ["01:0a:0f:08", "...", "..."]

        self.access_list = set()
        for hwid in config.get("access_list"):
            self.access_list.add(hwid.lower())

        # declare self as rfid_auth:
        dc.rfid_auth = self

    def setup(self):
        # self.api.setup()
        pass

    def enable(self):
        pass

    def disable(self):
        pass

    def teardown(self):
        pass

    def has_access(self, hwid_str, *args, **kwargs):
        """lookup detected hwid,"""
        # lookup hwid in db
        access = hwid_str in self.access_list
        logger.debug(f"RFID KEY lookup({hwid_str}): access={access}")
        return access
