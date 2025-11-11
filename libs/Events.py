import threading
from libs.data_container import data_container as dc


class EventSubscription:
    def __init__(self, e, i, f):
        self.e = e  # Events object
        self.i = i  # event_id
        self.f = f  # f_action

    def active(self):
        if self.e is not None:
            return self.e.exists(self.i, self.f)

    def cancel(self):
        """Cancel / Unsubscribe the event."""
        if self.e is not None:
            self.e.unsubscribe(self.i, self.f)

            # clear vars:
            self.f = None
            self.i = None
            self.e = None


class Events:
    #
    # _events[event_id] = [ f_action: function ]
    #
    def __init__(self):
        self._events = {}
        self.lock = threading.Lock()  # thread safety

    def subscribe(self, event_id, f_action):
        """subscribe to an event by 'event_id', and callback f_action."""
        dc.logger.debug("subscribe event '{}', f '{}'.".format(event_id, f_action))

        #  avoid duplicates,  check if already exists:
        with self.lock:
            if self.exists(event_id, f_action):
                return EventSubscription(self, event_id, f_action)

            # init event_id array if missing
            if event_id not in self._events:
                self._events[event_id] = []

            # add subscription
            self._events[event_id].append(f_action)

        # return EventSubscription object
        return EventSubscription(self, event_id, f_action)

    def exists(self, event_id, f_action):
        """check if event already exists"""
        if event_id in self._events and f_action in self._events[event_id]:
            return True

        return False

    def unsubscribe(self, event_id, f_action):
        """remove subscription"""
        with self.lock:
            if event_id in self._events:
                self._events[event_id].remove(f_action)

    def raise_event(self, event_id, data: dict = None, wait=False):
        """raise an event by event_id, and pass any data to the callback functions."""
        data = {} if data is None else data

        dc.logger.debug("raise_event '{}'.".format(event_id))
        t = []  # list of threads

        with self.lock:
            # run subscribtions paralel in threads.
            for event in self._events.get(event_id, []):
                # execute: event(data)
                t.append(threading.Thread(target=event, args=[data]))

        # start thread (outside .lock)
        for thread in t:
            thread.start()

        # wait untill all threads are finished
        if wait == True:
            for thread in t:
                thread.join()

    def debug_info(self):
        """print debug info about events and their subscribers."""
        print(
            "DEBUG EVENTBUS: event_id len:{} , obj:{} ".format(len(self._events), self)
        )

        with self.lock:
            for event_id in self._events:
                print(
                    "DEBUG event_id: '{}', number of subscribers: {}".format(
                        event_id, len(self._events[event_id])
                    )
                )
                for f_action in self._events[event_id]:
                    print(f"      event :'{event_id}'")
                    print(f"      action:'{f_action}{f_action.__doc__}'")
                    print("")


class StateSubscription:
    def __init__(self, s, f):
        self.s = s  # State object
        self.f = f  # f_action

    def active(self):
        if self.s is not None:
            return self.s.exists(self.f)

    def cancel(self):
        """Cancel / Unsubscribe the event."""
        if self.s is not None:
            self.s.unsubscribe(self.f)

            # clear vars:
            self.f = None
            self.s = None


class State:
    def __init__(self, value=None, set_logic=None):
        self._subscribers = []
        self._value = value
        self._logic = set_logic
        self.lock = threading.Lock()  # thread safety

    def set_logic(self, logic_callback=None):
        """set additional callback for manipulating the value before setting it.
        logic_callback must accept and return 1 argument: "lambda v: return v"
        """
        self._logic = logic_callback

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        # don't do anything when value is the same
        self.set(value)

    def set(self, value):
        with self.lock:
            if self._value is value:
                return

            if self._logic is not None:
                # run magic _logic callback to set value
                value = self._logic(value)

            # update value
            self._value = value

            # notify each subscribtion
            for callback in self._subscribers:
                # execute: callback_s(value)
                threading.Thread(target=callback, args=[value]).start()
                # start thread after lock.release...?

    def subscribe(self, f_action):
        """subscribe to state changes of the value of this object."""
        dc.logger.debug("subscribe State, f '{}'.".format(f_action))

        #  avoid duplicates,  only add when not exist:
        with self.lock:
            if not self.exists(f_action):
                self._subscribers.append(f_action)

                # set initial value
                f_action(self._value)

        return StateSubscription(self, f_action)

    def exists(self, f_action):
        """check if subscription already exists"""
        return f_action in self._subscribers

    def unsubscribe(self, f_action):
        """remove subscription"""
        with self.lock:
            if f_action in self._subscribers:
                self._subscribers.remove(f_action)

    def wait_for(self, match_value, timeout=-1):
        """Wait until value becomes 'match_value', then continue executing again."""
        # create lock in variable
        my_lock = threading.Lock()

        #  aquire lock
        my_lock.acquire()

        # put an lock.release() in callback and place it inside an subscription
        e = self.subscribe(
            lambda v: v == match_value and my_lock.locked() and my_lock.release()
        )

        # now wait until this lock is released by this lamda match callback, and we can acquire it again
        my_lock.acquire(timeout=timeout)

        # nice: done waiting, we are here now

        # cleanup subscription callback
        e.cancel()
