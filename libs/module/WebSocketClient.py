import websocket, ssl

from libs.data_container import data_container as dc
import time
from libs.Events import State, Events
import libs.Module as module
import threading

logger = dc.logger

import json


#
# TODO:
#
# [ ] get event names from solenoid module
# [ ] get api base_url from DjangoBackend... module
# [ ] set User-Agent


#
# set default config:
#
DEFAULT_CONFIG = {
    "allowed_events": [
        "open_solenoid",
        "cancel_open_solenoid",
        "toggle_permanent_open",
    ],
}


class WebSocketClient(module.BaseModule):
    def __init__(self, config={}):
        super().__init__(config)

        # Solenoid module TODO

        self.ws_url = "wss://localhost:4430/ws/lock.socket"
        self.thread = None

        self.ws = None

    def setup(self):
        pass

    # send json over websocket
    def send_json(self, data):
        try:
            js = json.dumps(data)
            logger.info(f"out: {js}")
            self.ws.send_text(js)
        except Exception as e:
            logger.info(f"Exception during websocket send ({data}).", exc_info=True)

    def serverside_comm_read(self):

        self.send_json({"event": "hello world... self"})

        # subscribtions:
        self.my_sub = []

        # solenoid state
        self.solenoid = dc.module.get("s1", None)

        if self.solenoid:
            self.my_sub.append(
                self.solenoid.state_open.subscribe(
                    lambda value: self.send_json({"var": {"state_open": value}})
                )
            )

            self.my_sub.append(
                self.solenoid.permanent_open_state.subscribe(
                    lambda value: self.send_json(
                        {"var": {"permanent_open_state": value}}
                    )
                )
            )

        # lockname: self.backend_api.lockname
        # url:
        self.backend_api = dc.rfid_auth.api

        # subscribe / send vars:
        var = {}
        try:
            var["state_open"] = self.solenoid.state_open.value
        except:
            logger.warning("failed websocket var: state_open", exc_info=True)
            var["state_open"] = None

        self.send_json({"event": "hello world... 3"})

        try:
            var["allow_permanent_open"] = self.solenoid.allow_permanent_open
        except:
            logger.warning("failed websocket var: allow_permanent_open", exc_info=True)
            var["allow_permanent_open"] = None

        try:
            var["permanent_open_state"] = self.solenoid.permanent_open_state.value
        except:
            logger.warning("failed websocket var: permanent_open_state", exc_info=True)
            var["permanent_open_state"] = -2

        try:
            var["lockname"] = self.backend_api.lockname
        except:
            logger.warning("failed websocket var: lockname", exc_info=True)
            var["lockname"] = "[name not set]"

        # send all variables
        self.send_json({"var": var})
        # we are ready/online: comm ready
        self.send_json({"comm": "ready"})

    def run(self):

        def ws_send_json(ws, data):
            try:
                js = json.dumps(data)
                logger.info(f"out: {js}")
                ws.send_text(js)
            except Exception as e:
                logger.info(f"Exception during websocket send ({data}).", exc_info=True)

        # events to bind to the websocket:
        def ws_on_open(ws):
            pass

        def ws_on_message(ws, message):
            logger.info(f"in: {message}")
            message = json.loads(message)

            # incomming event:
            if "event" in message:
                if message["event"] in DEFAULT_CONFIG["allowed_events"]:
                    dc.e.raise_event(message["event"])

            if "comm" in message and message["comm"] == "ready":
                self.serverside_comm_read()

        # connect websocket
        self.ws = websocket.WebSocketApp(
            "wss://localhost:4430/ws/lock.socket",
            on_open=ws_on_open,
            on_message=ws_on_message,
        )
        self.ws.run_forever(
            sslopt={"cert_reqs": ssl.CERT_NONE, "certfile": "./tmp/client.pem"}
        )

        # cleanup event subscribtions:
        for s in self.my_sub:
            s.cancel()

    def enable(self):
        if not (self.thread and self.thread.is_alive()):
            self.thread = threading.Thread(target=self.run, args=())
            self.thread.daemon = True  # Daemonize thread
            self.thread.start()  # Start the execution
            logger.info("start_thread - WebSocketClient")

        else:
            logger.info(
                "notice: WebSocketClient: start_thread, thread is already running "
            )

    def disable(self):
        # stop the loop
        if self.ws:
            self.ws.close()
            logger.info("stop_thread - WebSocketClient")

    def teardown(self):
        pass
