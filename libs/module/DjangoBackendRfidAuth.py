import requests
import simplejson as json
import threading
import datetime
import time
import hashlib
import os

from libs.Events import State

from libs.data_container import data_container as dc


class ApiError(Exception):

    def __init__(self, message, resp=None):
        self.message = message
        self.resp = resp

        if self.resp is not None:
            try:
                self.json = resp.json()
                raise Exception("inside ApiError", json.dumps(self.json, indent=4))
            except ValueError:
                raise Exception("No JSON !!!!", resp.content)
            except AttributeError:
                raise Exception("No JSON !!!!", resp.content)
        else:
            raise Exception("NO response data to display...")


class LogStats:
    def __init__(self, parent, precision=0, sync_interval=None):
        self.parent = parent
        self.table_key_last_seen = []
        self.table_unknown_key = []
        self.lock = threading.Lock()

        self.precision = (
            precision  # in seconds. will be devided in exact intervals since epoch
        )
        self.sync_interval = sync_interval if sync_interval else self.precision

        self.limit_post_entries = 1024

        # direct push sync
        self.direct_push_on_add = False
        self.next_sync = self.get_timestamps_now_begin_end(self.sync_interval)[2]

    def get_timestamps_now_begin_end(self, precision=None):
        """Get timestamps for logging: (now, begin, end)
        now: is now
        begin: is beginning of 'privacy friendly' time window set by self.precision
        end: is end of 'privacy friendly' time window set by self.precision
        """
        precision = precision if precision else self.precision
        t_now = datetime.datetime.now().timestamp()

        # int(timestamp / precision) * precision ==> timestamp of begin of this interval.
        if precision > 1:
            # precision is not 0
            t_begin = int(t_now / precision) * precision
            # set end off interval
            t_end = ((int(t_now / precision) + 1) * precision) - 0.000001
        else:
            t_begin = t_now
            # precision = 0
            t_end = t_now

        return (
            datetime.datetime.fromtimestamp(t_now, tz=datetime.timezone.utc),
            datetime.datetime.fromtimestamp(t_begin, tz=datetime.timezone.utc),
            datetime.datetime.fromtimestamp(t_end, tz=datetime.timezone.utc),
        )

    def add(self, key, known_key, meta_data: dict = None):
        # get privacy friendly timestamps, now , begin, end
        meta_data = {} if meta_data is None else meta_data

        t_now, t_begin, t_end = self.get_timestamps_now_begin_end()

        r = {}
        r["key"] = str(key)
        r["count"] = 1

        # UnknownKey
        if not known_key:
            # set timestamp
            r["timestamp"] = t_now.isoformat()

            # save:
            with self.lock:
                try:
                    # find existing one if exist
                    item = next(
                        item for item in self.table_unknown_key if item["key"] == key
                    )
                    item["count"] += r["count"]
                    item["timestamp"] = r["timestamp"]
                    item["meta_data_json"] = json.dumps(
                        {**meta_data, **json.loads(item["meta_data_json"])}
                    )
                except:
                    # add new
                    r["meta_data_json"] = json.dumps(meta_data)
                    self.table_unknown_key.append(r)

        # Key -> LastSeen table with obfuscated timestamp
        else:
            r["timestamp_begin"] = t_begin.isoformat()
            r["timestamp_end"] = t_end.isoformat()

            with self.lock:
                try:
                    # find existing one if exist
                    item = next(
                        item for item in self.table_key_last_seen if item["key"] == key
                    )
                    item["count"] += r["count"]
                    item["timestamp_begin"] = r["timestamp_begin"]
                    item["timestamp_end"] = r["timestamp_end"]
                except:
                    # add new
                    self.table_key_last_seen.append(r)

        if self.direct_push_on_add or not known_key:
            self.try_sync()

    def try_sync(self, flush=False):
        t_now, t_begin, t_end = self.get_timestamps_now_begin_end()
        # always sync unknown keys if available:
        with self.lock:
            if len(self.table_unknown_key) != 0:
                self.api_sync_unknownkeys()

            # knwon keys, only sync periodicly
            if len(self.table_key_last_seen) != 0:
                if flush or self.next_sync < t_now:
                    self.api_sync_keys_last_seen(flush)

            if len(self.table_key_last_seen) == 0:
                self.next_sync = self.get_timestamps_now_begin_end(self.sync_interval)[
                    2
                ]

    def api_sync_unknownkeys(self):
        unknownkeys = []
        for uk in self.table_unknown_key[: self.limit_post_entries]:
            unknownkeys.append(uk)

        try:
            resp = self.parent.request_post(
                f"/api/lock/log.unknownkeys", {"unknownkeys": unknownkeys}
            )
            dc.logger.debug(f"DEBUG: resp: {resp}")
        except Exception as e:
            dc.logger.warning(
                f"Network down?: api_sync_unknownkeys failed: {e.__class__.__name__}: {e}"
            )
            return

        dc.logger.info(
            f"unknownkeys synchronized: {len(resp.get('saved'))}/{len(unknownkeys)}, errors: {len(resp.get('err_msgs', []))}"
        )

        # log err_msgs in our error log:
        for err_msg in resp.get("err_msgs", []):
            dc.logger.error(f"unknownkeys err_msg[]: {err_msg}")

        # remove saved items from our list
        for item in resp.get("saved"):
            dc.logger.debug(f"remove item: {item}")
            self.table_unknown_key.remove(item)

    def api_sync_keys_last_seen(self, flush=False):
        keys_last_seen = []

        # collect entries to sync
        for k in self.table_key_last_seen[: self.limit_post_entries]:
            # if timestamp_end is newer then now: it's time to sync:
            keys_last_seen.append(k)

        if keys_last_seen:
            try:
                resp = self.parent.request_post(
                    f"/api/lock/log.keys_last_seen", {"keys_last_seen": keys_last_seen}
                )
                dc.logger.debug(f"DEBUG: resp: {resp}")
            except Exception as e:
                dc.logger.warning(
                    f"Network down?: api_sync_keys_last_seen failed: {e.__class__.__name__}: {e}"
                )
                return

            dc.logger.info(
                f"keys_last_seen synchronized: {len(resp.get('saved'))}/{len(keys_last_seen)}, errors: {len(resp.get('err_msgs', []))}"
            )

            # log err_msgs in our error log:
            for err_msg in resp.get("err_msgs", []):
                dc.logger.error(f"keys_last_seen err_msg[]: {err_msg}")

            # remove saved items from our list
            for item in resp.get("saved"):
                dc.logger.debug(f"remove item: {item}")
                self.table_key_last_seen.remove(item)

    def dump(self):
        print("table_unknown_key:")
        for r in self.table_unknown_key:
            print(json.dumps(r))

        print("table_key_last_seen")
        for r in self.table_key_last_seen:
            print(json.dumps(r))

        print(
            f"next sync in : {int(self.next_sync - self.get_timestamps_now_begin_end()[0])} seconds"
        )


#
# FingerprintAdapter for validating server SSL certificate
#
from requests.packages.urllib3.poolmanager import PoolManager


class _FingerprintAdapter(requests.adapters.HTTPAdapter):
    def __init__(self, fingerprint=None, **kwargs):
        self.fingerprint = str(fingerprint)
        super(_FingerprintAdapter, self).__init__(**kwargs)

    def init_poolmanager(self, *args, **kwargs):
        # print("self.fingerprint:", self.fingerprint)
        kwargs["assert_fingerprint"] = self.fingerprint
        super().init_poolmanager(*args, **kwargs)


#
# Main BackendApi class
#
class BackendApi:

    def __init__(
        self,
        api_url,
        offline_file=None,
        background_sync_method="LOOP",
        log_unknownkeys=True,
        log_stats_precision=0,
        log_sync_interval=None,
        server_ssl_fingerprint=None,
        client_ssl_cert=None,
    ):
        self.lockname = "init not-set"
        self.lock_disabled = State(value=True)

        self.synchronized = False
        # log unknownkeys
        self.log_unknownkeys = log_unknownkeys

        self.lock = threading.Lock()

        # self.keys = [False]
        self.keys = {"false": False}
        # self.disabled = False

        # self.log_stats = LogStats(self, 3600*24*7)
        self.log_stats = LogStats(self, log_stats_precision, log_sync_interval)

        self.auto_sync_secs = 60
        # set to break loop (force reload, start shutdown).
        self.auto_sync_loop_event = threading.Event()
        # set to stop loop from restarting.
        self.auto_sync_stop_event = threading.Event()

        # SSL things:
        # self.server_ssl_fingerprint = server_ssl_fingerprint
        # self.client_ssl_cert = client_ssl_cert

        # mount fingerprint adapter on reqeust Session
        self.api_url = api_url

        self.requests = requests.Session()
        self.requests.headers.update({"User-Agent": dc.app_name_ver})

        if server_ssl_fingerprint is None:
            raise Exception(
                f"server_ssl_fingerprint is not configured!, config the backend SSL fingerprint (you can find it in the backend admin.)"
            )

        # dc.logger.warn("!!!! _FingerprintAdapter is disabled")
        self.requests.mount(self.api_url, _FingerprintAdapter(server_ssl_fingerprint))
        self.requests_kwargs = {}  # = {'verify': False, 'cert': client_ssl_cert}
        self.requests.verify = False

        if client_ssl_cert is None:
            raise Exception(
                f"client_ssl_cert is not configured!, config the *.pem file you created with gencert.sh "
            )
        if not os.path.isfile(client_ssl_cert):
            raise Exception(
                f"client_ssl_cert '{client_ssl_cert}' is missing!!, create one with gencert.sh "
            )
        self.requests.cert = client_ssl_cert

        # create Configfile Integrity Check, to ensure valid operation when network is restored.
        self.cic = self.create_configfile_integrity_check(
            api_url, server_ssl_fingerprint, client_ssl_cert
        )

        # if offline_file
        self.offline_file = offline_file

        #  back_ground_sync [None, LOOP ]
        self.background_sync_method = background_sync_method

    def setup(self):
        # startup procedure for loading offline_file and syncing with backend:
        #
        # if offline_file is defined:
        #   - try to read file, if we fail we must sync before starting up.
        #   (this way we know for sure the backend settings are configured right)
        #   - after reading succesful we immediate try to sync. (but will not abort on temp failure, since backend settings are configured right).
        # if offline_file is false: (no keys are kept on storage)
        #   - we will try to sync, but if failed we keep running but stay in "lock_disabled" mode.
        #

        try:
            self.load_from_file()
        except Exception as e:
            dc.logger.warning(f"couldn't read offline_file: {e}")
            dc.logger.info(f"trying to sync with server to resolve this issue.")
            self.api_sync()

        if not self.offline_file:
            dc.logger.info(f"offline keys db is disabled (offline_file).")
            dc.logger.info(
                f"we must to download keys in memmory before we can enabled..."
            )

            try:
                self.api_sync()
            except Exception as e:
                dc.logger.warning(f"couldn't sync/download keys: {e}")

        if not self.synchronized:
            dc.logger.warning(f"Starting up without keys db: lock is in disabled mode!")

        # self.start_background_sync()
        # background sync will be started by DjangoBackendRfidAuth.enable()

    def dump(self):
        for k in self.keys.keys():
            print(f" * {k}:")
            if self.keys[k]["ruleset"]:
                for r in self.keys[k]["ruleset"]:
                    print(f"   - {r}")

    def create_configfile_integrity_check(
        self, api_url, server_ssl_fingerprint, client_ssl_cert
    ):
        # configfile integrity checks, to ensure valid operation when network is restored.
        cic = {}
        cic["api_url"] = api_url
        cic["server_ssl_fingerprint"] = server_ssl_fingerprint
        cic["client_ssl_fingerprint"] = make_sslfingerprint(client_ssl_cert)
        return str(cic)

    def load_from_file(self):
        if self.offline_file is False:
            dc.logger.info(f"offline_file is disabled (keys not loading from file).")
            return

        with self.lock:
            dc.logger.info(f"read keys database from file: '{self.offline_file}';")
            # open json file
            with open(self.offline_file, "r") as json_file:
                # Reading from file
                data = json.load(json_file)

                # validate cic (Configfile Intergity Check)
                if data.get("cic") != self.cic:
                    raise Exception(
                        f"{self.offline_file}': Configfile Intergity Check failed: api_url,server_ssl_fingerprint or client_ssl doesn't match with config. Need server sync before operation!."
                    )

                # set lockname:
                self.lockname = data.get("lockname", "not-set")
                dc.logger.info(f"read keys db for lockname  : '{self.lockname}' ")

                # simply overwrite dict:
                self.keys = data.get("keys")
                dc.logger.info(
                    f"read keys database, entries: '{len(self.keys)}' keys loaded."
                )
                dc.logger.info(f"read keys database, hash   : '{self.keys_hash()}' ")

                # lock_disabled, or if missing guess the answer on the numer of keys.
                self.lock_disabled.value = data.get(
                    "lock_disabled", not bool(len(self.keys))
                )
                dc.logger.info(f"read lock disabled: {self.lock_disabled.value}.")

    def save_to_file(self):
        if self.offline_file is False:
            dc.logger.debug(f"offline_file is disabled (not saving to file).")
            return

        with self.lock:
            dc.logger.info(f"write keys database to file {self.offline_file}_tmp")
            data = {}
            data["lockname"] = self.lockname
            data["keys"] = self.keys
            data["lock_disabled"] = self.lock_disabled.value

            # add cic (Configfile Intergity Check)
            data["cic"] = self.cic

            # write to tmp file
            with open(self.offline_file + "_tmp", "w") as json_file:
                json.dump(data, json_file)

            # rename tmp file
            if os.path.isfile(self.offline_file):
                os.remove(self.offline_file)

            os.rename(self.offline_file + "_tmp", self.offline_file)

            dc.logger.info(f"written keys database to file : '{self.offline_file}';")
            dc.logger.info(
                f"written keys database, entries: '{len(self.keys)}' keys loaded."
            )
            dc.logger.info(f"written keys database, hash   : '{self.keys_hash()}' ")

    def start_background_sync(self):
        """
        start background thread using 'self.background_sync_method'
        """

        if not self.background_sync_method:
            dc.logger.info(f"background_sync is disabled. ")
            return

        def auto_sync_target(self):
            """threading target"""

            dc.logger.info("LOOP: start auto_sync_target")
            while not self.auto_sync_stop_event.is_set():
                try:
                    # sync keys
                    self.api_sync()
                    # emit event sucess
                    dc.e.raise_event("sync_success")

                except Exception as e:
                    mesg = f"exception occured during background keys sync. (exception ignored)"
                    dc.logger.warning(mesg, exc_info=e)
                    # emit event fail/log
                    dc.e.raise_event("sync_fail_log", {"mesg": mesg, "exception": e})

                try:
                    # try sync last_seen and unknown_keys
                    self.log_stats.try_sync()

                except Exception as e:
                    mesg = f"exception occured during background log_stats sync. (exception ignored)"
                    dc.logger.warning(mesg, exc_info=e)
                    # emit event fail/log
                    dc.e.raise_event("sync_fail_log", {"mesg": mesg, "exception": e})

                # sleep until next auto_sync_loop
                dc.logger.debug(
                    f"auto sync loop sleeps for {self.auto_sync_secs} seconds."
                )

                self.auto_sync_loop_event.wait(
                    timeout=self.auto_sync_secs
                )  # use event.wait instead of time.sleep.

                # make sure the loop event is cleared
                self.auto_sync_loop_event.clear()

            dc.logger.info("LOOP: auto_sync_target stopped!")

        methods = {}
        methods["LOOP"] = auto_sync_target

        try:
            target_method_def = methods[self.background_sync_method]
        except KeyError:
            raise KeyError(
                f"background_sync_method = '{self.background_sync_method}' not found. (must be value of {methods.keys()})"
            )

        with self.lock:
            # are we already running?
            if hasattr(self, "auto_sync_thread") and self.auto_sync_thread.is_alive():
                return self.auto_sync_thread

            self.auto_sync_stop_event.clear()
            self.auto_sync_thread = threading.Thread(
                target=target_method_def, args=(self,)
            )
            self.auto_sync_thread.start()

            return self.auto_sync_thread

    def stop_background_sync(self, join=False):
        with self.lock:
            if not self.auto_sync_stop_event.is_set():
                dc.logger.debug(
                    f"DEBUG: auto_sync will stop... {self.auto_sync_stop_event.is_set()}"
                )
                # stop the loop from restarting
                self.auto_sync_stop_event.set()
                # stop this loop
                self.auto_sync_loop_event.set()

        if join:
            dc.logger.debug(
                f"DEBUG: join thread... {getattr(self, 'auto_sync_thread', 'not-set')}"
            )
            if hasattr(self, "auto_sync_thread"):
                self.auto_sync_thread.join()

        # self.auto_sync_thread

    def force_reload(self):
        with self.lock:
            if not self.auto_sync_stop_event.is_set():
                dc.logger.debug("force reload sync")
                # set event to restart the loop
                self.auto_sync_loop_event.set()

            else:
                dc.logger.info("force_reload ignored, background sync not running.")

    def cleanup(self):
        # order background thread to stop
        self.stop_background_sync(join=False)

        # try sync last_seen and unknown_keys
        self.log_stats.try_sync(flush=True)

        # join thread to
        self.stop_background_sync(join=True)

    def __del__(self):
        dc.logger.debug(f"DEBUG: '{self}.__del__()' called!")
        self.cleanup()

    def keys_hash(self):
        return hashlib.new(
            "SHA256", json.dumps(self.keys, sort_keys=True).encode("utf-8")
        ).hexdigest()

    def acl_parse_rule(self, rule):
        now = datetime.datetime.now().astimezone()

        # Note that after/before are expected to have a timezone
        # specifier and are interpret as absolute timestamps, while
        # time_start/time_end are just plain times and are interpreted
        # in the local timezone (independent of the server timezone).
        after = rule.get("after", None)
        before = rule.get("before", None)
        weekdays = rule.get("weekdays", [])
        time_start = rule.get("time_start", None)
        time_end = rule.get("time_end", None)
        #
        # rules of this rules (self, not child/parent)
        #

        # false if after newer than now
        if after is not None:
            if datetime.datetime.fromisoformat(after) > now:
                return False, "after newer than now"

        # false if before older than now
        if before is not None:
            if datetime.datetime.fromisoformat(before) < now:
                return False, "before older than now"

        # false if is now.weekday() is not in weekdays
        # if rule.weekdays is not None and now.weekday() not in rule.weekdays:
        if now.weekday() not in weekdays:
            return False, "today not in weekdays"

        # false if now.time is before time_start
        if time_start is not None:
            if now.time() < datetime.time.fromisoformat(time_start):
                return False, "now is before time_start"

        # false if now.time is after time_end
        if time_end is not None:
            if now.time() > datetime.time.fromisoformat(time_end):
                return False, "now is after time_end"

        # nothing return false so we are OK
        return True, "nothing failed"

    def acl_has_access(self, hwid):
        # ruleset = self.keys.get(key,{}).get('ruleset',[])
        ruleset = self.keys[hwid]["ruleset"]

        for rule in ruleset:
            dc.logger.debug(f"DEBUG: { len(ruleset) },  {rule}")
            (acces, reason) = self.acl_parse_rule(rule)
            if acces is True:
                return (acces, reason)

        # no condition return true
        return False, "no condition in ruleset returned true"

    def lookup(self, key, target, nfc_tools, *args, **kwargs):
        key = key.lower()  # lowercase this key
        meta_data = {}  # placeholder for meta_data

        if self.lock_disabled.value is True:
            msg = "Warning: lock disabled or never synchronised, lookup() and last-seen logging ignored."
            dc.logger.warning(msg)
            return False, msg

        # lookup key in access list:
        if key not in self.keys:
            has_access, msg = False, "Not found"
            known_key = False
            meta_data = nfc_tools.collect_meta()
            dc.logger.info(f"card meta info: {meta_data}")
        else:
            # need meta data?
            if self.keys[key].get("need_meta_data", False):
                dc.logger.info(f"key ('{key}') need_meta_data")

                try:
                    # read meta data
                    meta_data = nfc_tools.collect_meta()
                    # post meta_data to backend
                    self.api_key_merge_meta_data_json(key, json.dumps(meta_data))
                    # all succeeded: del 'need_meta_data':
                    del self.keys[key]["need_meta_data"]

                except Exception as e:
                    # Soft failing: collect_meta().
                    # since we haven't fully tested our collect_meta() feature, and we never want
                    # to lockout users who have access. we "soft fail" when reading of meta_data
                    # failed.
                    #
                    # Ideally when this works perfect, we don't want to supress the exceptions, so
                    # that for example TargetGoneWhileReadingError will fail access and notify the
                    # end user to prompt their NFC key again to the reader.
                    #
                    # raise(e) # comment/uncomment to enable/disable softfail
                    dc.logger.info(
                        f"Soft failed: nfc_tools.collect_meta: {e}", exc_info=e
                    )

            # has access comform access rule?
            has_access, msg = self.acl_has_access(key)
            known_key = True

        # keep last_seen list
        if known_key or (not known_key and self.log_unknownkeys):
            self.log_stats.add(key, known_key, meta_data)
        else:
            dc.logger.debug("Logging is disabled by log_unknownkeys.")

        return has_access, msg

    def request_post(self, path, data: dict):
        url = self.api_url + path

        dc.logger.debug(f"DEBUG POST:  {data}")
        resp = self.requests.post(url, json=data)

        if resp.status_code != 200:
            # This means something went wrong.
            raise ApiError("POST {}/ {}".format(url, resp.status_code), resp)

        return resp.json()

    def api_key_merge_meta_data_json(self, key, meta_data_json="{}"):
        """
        api request to merge meta_data_json with key.
        returns boolean True on succes, False or None on error.
        """
        try:
            resp = self.request_post(
                f"/api/key/merge.meta_data_json",
                {"key": key, "meta_data_json": meta_data_json},
            )
            dc.logger.debug(f"DEBUG: resp: {resp}")
            # api should return saved=True | saved=False
            return resp.get("saved", None)
        except Exception as e:
            dc.logger.warning(
                f"Unexpected Exception during api_key_merge_meta_data_json. {e}",
                exc_info=e,
            )

    def api_sync(self):
        """sync with backend."""

        max_loop = 3  #

        with self.lock:
            #
            # check if we are up to date
            #
            keys_hash = self.keys_hash()
            resp = self.request_post(f"/api/lock/sync.keys", {"keys_hash": keys_hash})
            dc.logger.debug(f"DEBUG: resp: {resp}")
            force_write_offlinedb = False

            # set or update lockname:
            if self.lockname != resp.get("lockname", "not-set"):
                self.lockname = resp.get("lockname", "not-set")
                force_write_offlinedb = True

            dc.logger.info(f"sync keys db for lockname  : '{self.lockname}' ")

            # show message in logs
            self.lock_disabled.value = bool(resp.get("disabled", False))
            if self.lock_disabled.value == True:
                dc.logger.warning("Warning: lock is disabled")

            # keys: -> update
            # while 'keys' in resp:
            self.synchronized = bool(resp.get("synchronised", False))
            while self.synchronized is not True:
                if max_loop <= 0:
                    dc.logger.warning(
                        "max loop detected, aborting sync action for now... and oppperate like nothing happend"
                    )
                    dc.logger.debug("info keys:", self.keys)
                    return ()

                # simply overwrite dict:
                self.keys = resp.get("keys")

                resp = self.request_post(
                    f"/api/lock/sync.keys", {"keys_hash": self.keys_hash()}
                )
                dc.logger.debug(f"DEBUG: resp: {resp}")

                # update synchronized
                self.synchronized = bool(resp.get("synchronised", False))

                # show message in logs
                self.lock_disabled.value = resp.get("disabled", False)
                if self.lock_disabled.value == True:
                    dc.logger.warning("Warning: lock is disabled")

                max_loop = max_loop - 1  # decrement our loop counter

            # synchronized
            if self.synchronized is True:
                dc.logger.info(
                    f"Info: we are synchronized. (hash: '{self.keys_hash()}')"
                )
            else:
                # some error
                if "error" in resp:
                    # something went wrong:
                    raise Exception(f"Error: error:{resp.get('error')}")
                else:
                    # something went wrong without even an error message:
                    raise Exception("Some fatal error, we don't understand:", resp)

        # if hash changed, save changes to file
        if self.keys_hash() != keys_hash or force_write_offlinedb:
            self.save_to_file()


class DjangoBackendRfidAuth:
    def __init__(self, config: dict):

        # init BackendApi with config:
        #
        # [module.rfid_auth]
        # type = "DjangoBackendRfidAuth"
        # api_url=
        # offline_file=None
        # background_sync_method='LOOP'
        # log_unknownkeys=True
        # server_ssl_fingerprint=None
        # client_ssl_cert=None

        #  api_url, offline_file=None, background_sync_method='LOOP', log_unknownkeys=True, server_ssl_fingerprint=None, client_ssl_cert=None
        kwargs = config.copy()
        del kwargs["type"]  # delete unwanted argument

        if "lockname" in kwargs:
            dc.logger.warning(
                f"DEPRECATED: config option 'lockname' is no longer in use."
            )
            del kwargs["lockname"]  # delete unwanted argument

        self.conf = kwargs

        self.api = BackendApi(**kwargs)

        # set rfid_auth in global data container, so that self.has_access is available.
        dc.rfid_auth = self

        # my event subscriptions, to cleanup on teardown.
        self.subscriptions = set()

        # add force_reload event.
        self.subscriptions.add(
            dc.e.subscribe("force_reload", dc.rfid_auth.force_reload)
        )

        # add kill -HUP support:
        self.subscriptions.add(dc.e.subscribe("app.sighup", self.force_reload))

    def setup(self):
        self.api.setup()

    def enable(self):
        self.api.start_background_sync()

    def disable(self):
        self.api.stop_background_sync(join=True)

    def teardown(self):
        # clearnup subscriptions:
        for subscription in self.subscriptions:
            subscription.cancel()

        self.api.cleanup()

    def force_reload(self, data: dict):
        self.api.force_reload()

    def has_access(self, hwid_str, target, nfc_tools, *args, **kwargs):
        """lookup detected hwid,"""
        # lookup hwid in db
        access, msg = self.api.lookup(hwid_str, target, nfc_tools, *args, **kwargs)
        dc.logger.debug(
            f"'{self.api.lockname}' RFID KEY lookup({hwid_str}): access={access} : {msg}"
        )
        return access


#
# SSL Extra's make_sslfingerprint
#


def make_sslfingerprint(cert_file):

    import base64
    import hashlib

    # read file into str
    with open(cert_file, "r") as f:
        cert = f.read()

    # find begin
    begin_cert = cert.find("-----BEGIN CERTIFICATE-----") + 27
    end_cert = cert.find("-----END CERTIFICATE-----")

    if begin_cert == -1 or end_cert == -1:
        raise Exception(
            "No Certificate found! ('-----BEGIN CERTIFICATE-----' and '-----END CERTIFICATE-----' are missing )"
        )

    return hashlib.sha256(base64.b64decode(cert[begin_cert:end_cert])).hexdigest()
