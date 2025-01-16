import libs.Module as module
from libs.data_container import data_container as dc
import requests

logger = dc.logger


class Healthchecks(module.BaseModule):
    """
    https://healthchecks.io based monitoring.
    """

    def __init__(self, config={}):
        super().__init__(config)

        # event
        self.url = config.get("url", None)

        if not self.url:
            logger.warning(f"Heathcheck failed: no url configured.")
            return

        #
        # setup/enable, we setup all logic here, since we want to be available right from the start.
        #
        logger.info(f"Heathcheck with url: '{self.url}'")

        #
        # connect event to our callback
        #

        # libs/module/DjangoBackendRfidAuth.py events:
        dc.e.subscribe("sync_success", lambda data: self.healthcheck_ping())
        dc.e.subscribe("sync_fail_log", lambda data: self.healthcheck("log", data))

        # libs/Module.py
        dc.e.subscribe(
            "app_startup_complete", lambda data: self.healthcheck("start", data)
        )
        dc.e.subscribe("app_abort", lambda data: self.healthcheck("fail", data))
        dc.e.subscribe("app_exit", lambda data: self.healthcheck("log", data))

    def setup(self):
        pass

    def enable(self):
        pass

    def disable(self):
        pass

    def teardown(self):
        pass

    def healthcheck_ping(self):
        """send ping, only if dc.module.app_startup_complete is True."""
        if dc.module.app_startup_complete:
            self.healthcheck()
        else:
            # operation is not proper, ignore this ping.
            logger.info(
                f"Heathcheck ping ignored: app_startup_complete hasn't completed or abort/exit has started."
            )

    def healthcheck(self, signal="", data={}):
        """
        Send ping or other signal with data.
        - signal see https://healthchecks.io/docs/http_api/

        - request-body will be made from:
            - data['mesg']
            - data['exception']

        """
        url = f"{self.url}"
        url += f"/{signal}"

        try:
            # prepare message body with mesg and data:
            msg_body = ""

            for key in ["mesg", "exception"]:
                if key in data:
                    msg_body += f"{key}: {data[key]}\n"

            # do healthcheck request
            requests.post(
                url, msg_body, headers={"User-Agent": dc.app_name_ver}, timeout=10
            )
            logger.info(f"Heathcheck call: '{signal}', '{data}'")

        except requests.RequestException as e:
            logger.warning(f"Heathcheck failed ({url}, '{data}'): {e}")
