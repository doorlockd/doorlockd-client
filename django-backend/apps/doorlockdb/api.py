#
# Ninja api
#
from asyncio.log import logger
from dataclasses import dataclass
from .models import *


from ninja import NinjaAPI, Schema
from typing import List

from django.core import serializers


#
# client SSL certificate authentication
#
class LockAuhClientSSL:
    #
    # this class will work like classes from ninja.security
    #
    def __call__(self, request):
        return Helpers.AuthWithByClientSSL(request)


api = NinjaAPI(auth=LockAuhClientSSL())


@api.exception_handler(Helpers.ErrorClientSSLCert)
def on_client_ssl_cert_error(request, exc):
    return api.create_response(
        request, {"error": f"Client SSL Certificate error :'{exc}'"}, status=401
    )


#
#  endpoint handlers:
#
@api.get("/lock/")
def locks(request):
    """Get some information about a lock."""
    # get Lock from authentication
    l = request.auth

    # return serializers.serialize("json", Lock.objects.all())
    # return serializers.serialize("python", Lock.objects.filter(id=lock_id))
    return serializers.serialize("python", [l])[0]


class ErrorOutputSchema(Schema):
    error: str


class SyncKeysInputSchema(Schema):
    keys_hash: str


class SyncKeysOutputSchema(Schema):
    keys: dict = None
    synchronised: bool = None
    disabled: bool = None


@api.post(
    "/lock/sync.keys", response={200: SyncKeysOutputSchema, 401: ErrorOutputSchema}
)
def api_lock_sync_keys(request, input_data: SyncKeysInputSchema):
    """Synchronise keys accesslist"""
    # return 'keys' OR 'synchronised' OR 'error'.
    # keys:           -> client must update key list
    # synchronised:   -> if value is true , client is up to date.
    # disabled:       -> additional bool value, if lock is disabled. (client must show warning in logs on lock)

    # 401:
    # error:          -> error message.

    # get Lock from authentication
    l = request.auth

    # init response dict
    resp = {}

    # if lock disabled (client will update to empty keys list):
    if not l.is_enabled:
        # we just add an additional error mesage to the response
        resp["disabled"] = True

    # store keys_on_lock so we know the current config on the lock
    sync, created = SyncLockKeys.objects.get_or_create(lock=l)
    out_of_sync, db_keys_config = sync.compare_hash_and_sync(input_data.keys_hash)

    # compare list
    # out_of_sync, db_keys_config = sync.out_of_sync()
    if out_of_sync:
        # out of sync:
        return {**resp, "message": "need update", "keys": db_keys_config}
    else:
        # in sync
        return {**resp, "message": "ok", "synchronised": True}


class LogUnknownKeySchema(Schema):
    key: str
    timestamp: str  # 'datetime.datetime.fromtimestamp(datetime.datetime.utcnow().timestamp()).isoformat()'
    count: int


class LogUnknownKeysOutputSchema(Schema):
    saved: List[LogUnknownKeySchema]


class LogUnknownKeysInputSchema(Schema):
    unknownkeys: List[LogUnknownKeySchema]


#
# Sync unknownkeys
#
@api.post(
    "/lock/log.unknownkeys",
    response={200: LogUnknownKeysOutputSchema, 401: ErrorOutputSchema},
)
def api_lock_log_unknownkeys(request, input_data: LogUnknownKeysInputSchema):
    """Post unknown_keys statistics"""
    saved = []

    # get Lock from authentication
    l = request.auth

    # proces input list of dicts[{'key': hwid, 'timestamp': ..., 'count': int}]
    for uk in input_data.unknownkeys:
        try:
            LogUnknownKey.register(uk.key, l, uk.timestamp, uk.count)
            saved.append(uk)
        except Exception as e:
            raise Exception(e)

    return {"saved": saved}


#
# Log Last Seen:
#
class LogKeysLastSeenSchema(Schema):
    key: str
    timestamp_begin: str  # 'datetime.datetime.fromtimestamp(datetime.datetime.utcnow().timestamp()).isoformat()'
    timestamp_end: str  # 'datetime.datetime.fromtimestamp(datetime.datetime.utcnow().timestamp()).isoformat()'
    count: int


class LogKeysLastSeenOutputSchema(Schema):
    saved: List[LogKeysLastSeenSchema]


class LogKeysLastSeenInputSchema(Schema):
    keys_last_seen: List[LogKeysLastSeenSchema]


@api.post(
    "/lock/log.keys_last_seen",
    response={200: LogKeysLastSeenOutputSchema, 401: ErrorOutputSchema},
)
def api_lock_log_keys_last_seen(request, input_data: LogKeysLastSeenInputSchema):
    """Post keys statistics"""
    saved = []

    # get Lock from authentication
    l = request.auth

    # LogKeyLastSeen.addLastSeen(hwid, lock, last_seen_start=None, last_seen_end=None, count=1):
    # proces input list of dicts[{'key': hwid, 'timestamp': ..., 'count': int}]
    for k in input_data.keys_last_seen:
        try:
            LogKeyLastSeen.addLastSeen(
                k.key, l, k.timestamp_begin, k.timestamp_end, k.count
            )
            saved.append(k)
        except Exception as e:
            raise Exception(e)

    return {"saved": saved}


#
# wait for an event. Long poll request
#
@api.post("lock/event.long_poll")
def api_lock_event_long_poll(request):
    """Attemp to create a long_poll request in Ninja api:
    this endpoint will wait for max ~500s before returning an event.
    """
    data = {}

    # get Lock from authentication
    lock = request.auth

    # get Sync object from db
    sync, created = SyncLockKeys.objects.get_or_create(lock=lock)

    resp = {}
    import datetime
    import time

    for c in range(0, 100):
        # counter for debug purpose
        resp["c"] = c
        resp["t"] = datetime.datetime.isoformat(datetime.datetime.now())

        # check sync state:
        sync.refresh_from_db()
        if not sync.synchronized:
            return {**resp, "event": "sync", "synchronized": sync.synchronized}

        time.sleep(5)

    return {**resp, "event": "no_event"}
