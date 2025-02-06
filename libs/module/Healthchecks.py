import libs.Module as module
from libs.data_container import data_container as dc
import requests
import traceback

logger = dc.logger


class Healthchecks(module.BaseModule):
    """
    https://healthchecks.io based monitoring.
    """

    def __init__(self, config={}):
        super().__init__(config)

        # event
        self.url = config.get("url", None)

        # endpoints[ {'signal': ['event_to_list_to', 'more_events', ..]}, ... ]
        self.endpoint = config.get("endpoint", [])

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
        if not self.endpoint:
            logger.warning(
                f"Heathcheck has no endpoints configured! (for url '{self.url}')"
            )

        #
        for signal in self.endpoint:

            # register events
            if self.endpoint[signal]:

                # lambda callback using signal=signal to capture loop variable by value instead of reference.
                callback_fn = lambda data, signal=signal: self.healthcheck(signal, data)
                for event in self.endpoint[signal]:
                    dc.e.subscribe(event, callback_fn)
                    logger.info(
                        f"Heathcheck connected event: '{event}' to  signal: '{signal}'"
                    )

            else:
                logger.warning(
                    f"Heathcheck 'endpoint.{signal}' has no events configured! (for url '{self.url}')"
                )

    def setup(self):
        pass

    def enable(self):
        pass

    def disable(self):
        pass

    def teardown(self):
        pass

    def healthcheck(self, signal="ping", data={}):
        """
        Send ping or other signal with data.
        - signal 'ping' means no specific signal
        see https://healthchecks.io/docs/http_api/

        - request-body will be made from:
            - data['mesg']
            - data['exception']

        """

        # we also accept 'ping' as empty signal name , so it doesn't look ugly in our toml config
        if signal == "ping":
            signal = ""

        #
        # send ping, only if dc.module.app_startup_complete is True.
        #
        if signal == "":
            if not dc.module.app_startup_complete:
                # app is not opperating proper, ignore this ping.
                logger.info(
                    f"Heathcheck ping ignored: app_startup_complete hasn't completed or abort/exit has started."
                )
                return

        # construct endpoint url
        url = f"{self.url}/{signal}"

        try:
            # prepare message body with mesg and data:
            msg_body = ""

            for key in ["mesg", "exception"]:
                if key in data:
                    msg_body += f"{key}: {data[key]}\n"

            if "exception" in data:
                try:
                    tb = "".join(traceback.format_exception(data["exception"]))
                    msg_body += f"traceback:\n{tb}\n"
                except Exception as e:
                    msg_body += f"traceback: traceback failed ({e})\n"

            # do healthcheck request
            requests.post(
                url, msg_body, headers={"User-Agent": dc.app_name_ver}, timeout=10
            )
            logger.debug(f"Heathcheck call: '{signal}', '{data}'")

        except requests.RequestException as e:
            logger.warning(f"Heathcheck failed ({url}, '{data}'): {e}")
