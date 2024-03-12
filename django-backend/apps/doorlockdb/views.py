# from django.shortcuts import render

# Create your views here.
from asyncio.proactor_events import _ProactorBasePipeTransport
from faulthandler import is_enabled

# from tkinter import E
from django.http import HttpResponse, JsonResponse, StreamingHttpResponse

from apps.doorlockdb.model_forms import PersonForm
from .models import *
from django.http import Http404, HttpResponseForbidden
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import csrf_exempt

from django.core import serializers
from django.db.models import *

# from typing import Any

from .model_forms import KeyForm, LockForm, PersonForm, LogUnknownKeyForm

# login
from django.contrib.auth.decorators import login_required

import json
import time  # long_poll

import logging

logger = logging.getLogger(__name__)

# auth:
from django.conf import settings
from django.shortcuts import redirect


def auth_by_client_ssl(request):
    try:
        client_cert = request.META["HTTP_X_SSL_RAW_CERT"]
    except:
        # raise Exception("no client certificate found (HTTP_X_SSL_RAW_CERT missing)")
        return 'Exception("no client certificate found (HTTP_X_SSL_RAW_CERT missing)")'

    try:
        # lc = LockCertificate.objects.get(certificate=client_cert)
        l = Lock.objects.get(certificate=client_cert)
        return l
    except Exception as e:
        return e
    # return (client_cert)


def index(request):
    return HttpResponse(f'Doorlockd <a href="/admin">admin</a>.\n')


def generator_poll_events(lock):
    # get Sync object from db
    sync, created = SyncLockKeys.objects.get_or_create(lock=lock)

    resp = {}
    yield (json.dumps({**resp, "event": "ping", "message": "start long poll"}) + "\n")
    import datetime

    for c in range(0, 100):
        # counter for debug purpose
        resp["c"] = c
        resp["t"] = datetime.datetime.isoformat(datetime.datetime.now())

        # check sync state:
        sync.refresh_from_db()
        if not sync.synchronized:
            yield (
                json.dumps({**resp, "event": "sync", "synchronized": sync.synchronized})
                + "\n"
            )
        else:
            # ping to keep alive
            yield (json.dumps({**resp, "event": "ping"}) + "\n")

        # yield('\n\n')
        # yield(json.dumps({**resp, 'event': 'extra'}) + '\n')
        time.sleep(5)


def api_poll_events(request):
    try:
        l = Helpers.AuthWithByClientSSL(request)
    except Helpers.ErrorClientSSLCert as e:
        raise e

    # # if lock disabled (client will update to empty keys list):
    # if not l.is_enabled:
    #     # we just add an additional error mesage to the response
    #     JsonResponse({'disabled': True, 'error': 'Lock disabled'})
    # client will receive disabled values over a sync request.

    return StreamingHttpResponse(generator_poll_events(l))


@login_required(login_url="/admin/login/")
def details_person(request, person_id):
    if not request.user.has_perm("doorlockdb.view_person"):
        return HttpResponse("Oeps ... no permision to view person")

    person = get_object_or_404(Person, pk=person_id)

    locks = Lock.objects.all()
    person.set_check_any_out_of_sync(locks)

    return render(request, "details_person.html", {"person": person})


@login_required(login_url="/admin/login/")
def details_access(request):
    if not request.user.has_perm("doorlockdb.view_person"):
        return HttpResponse("Oeps ... no permision to view person")

    locks = Lock.objects.all()
    persons = Person.objects.all()

    # set cache method:
    for p in persons:
        p.set_check_any_out_of_sync(locks)

    return render(request, "details_access.html", {"persons": persons, "locks": locks})


@login_required(login_url="/admin/login/")
def details_lock(request, lock_id):
    if not request.user.has_perm("doorlockdb.view_lock"):
        return HttpResponse("Oeps ... no permision to view lock")

    lock = get_object_or_404(Lock, pk=lock_id)
    return render(request, "details_lock.html", {"lock": lock})
