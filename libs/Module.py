import libs.IOWrapper as IO
from libs.data_container import data_container as dc
import time
from libs.Events import State, Events
import threading
import importlib


logger = dc.logger


class BaseModule:
    # __init__(config={}): 	initialize myself
    # setup():				setup module:  (grab io_port from dc.io_port)
    # enable():				enable module: (io ports.setup / connect event callbacks)
    # disable():			disable module: (io ports.output(IO.LOW) / cancel events)
    # teardown():			de-setup module: cleanup ports

    def __init__(self, config={}):
        # initialize myself
        self.events = Events()
        # logger.info("init super BaseModule")

    def setup(self):
        # first stage of setup
        # grab io_port from dc.io_port
        raise NotImplementedError("setup() method not implemented in this Module")

    def enable(self):
        # # enable module
        # self.io_output.setup(IO.OUTPUT)
        #
        # # connect event to our callback
        # self.event = dc.e.subscribe(self.event_name, self.action_callback)
        raise NotImplementedError("enable() method not implemented in this Module")

    def disable(self):
        # # disable module
        # # cancel event
        # self.event.cancel()
        #
        # # set output low
        # self.io_output.output(IO.LOW)
        raise NotImplementedError("disable() method not implemented in this Module")

    def teardown(self):
        # # de-setup module
        # # cleanup ports
        # self.io_output.cleanup()
        raise NotImplementedError("teardown() method not implemented in this Module")


class ModuleManager:
    modules = {}
    _base_path = "libs.module."
    abort_event = threading.Event()

    def load_all(self, configs):
        t = []  # list of threads

        for mod_name in configs:
            # get module config
            mod_config = configs.get(mod_name)
            # mod_config['id'] = mod_name # add module id to the config

            mod_type = mod_config["type"]  # set mod_type

            if not mod_config.get("skip", False):
                logger.info("initializing module {} {}...".format(mod_type, mod_name))

                # spawn: self.load_mod(mod_name, mod_type, mod_config)
                t.append(
                    threading.Thread(
                        target=self.load_mod, args=[mod_name, mod_type, mod_config]
                    )
                )
                t[-1].start()

            # wait untill all threads are finished
            for thread in t:
                thread.join()

    def load_mod(self, mod_name, mod_type, mod_config):
        """load module by 'mod_name' (reference name), 'mod_type' (python module filename), 'mod_config' (config dictionary)"""
        logger.info("initializing module {} {}...".format(mod_name, mod_type))

        # import python module file
        mod = importlib.import_module(self._base_path + mod_type)
        # get class (same name as file)
        klass = getattr(mod, mod_type)
        # init object from class
        self.modules[mod_name] = klass(config=mod_config)

        return self.modules[mod_name]

    def get(self, mod_name, default=None):
        """return module by name, or return "default." """
        return self.modules.get(mod_name, default)

    def do(self, module, task):
        """module: index key of self.module[] , task: setup/enable/disable/teardown"""
        logger.info(
            "{} module {} {}...".format(
                task, self.modules[module].__class__.__name__, module
            )
        )
        try:
            getattr(self.modules[module], task)()  # call method on module
        except Exception as e:
            self.abort(f"Uncaught exception in {module} during {task}", exception=e)

    def do_all(self, task):
        """task: setup/enable/disable/teardown"""
        # for module in self.modules:
        # 	self.do(module, task)

        # run task paralel in threads.
        t = []  # list of threads
        for module in self.modules:
            # spawn: self.do(module, task)
            t.append(threading.Thread(target=self.do, args=[module, task]))
            t[-1].start()

        # wait untill all threads are finished
        for thread in t:
            thread.join()

        # abort_event is_set, some exception(s) occured, raise exception
        if self.abort_event.is_set() and task not in ("disable", "teardown"):
            raise Exception(f"abort_event is set, exception occured during {task}.")

    def abort(self, mesg, exception=None):
        if exception:
            logger.warning(f"abort(): {mesg} exception={exception}", exc_info=exception)
        else:
            logger.warning(f"abort(): {mesg}")

        self.abort_event.set()

    # def setup_all(self):
    # 	for module in self.modules:
    # 		logger.info('setup module {} {}...'.format(self.modules[module].__class__.__name__, module))
    # 		self.modules[module].setup()
    #
    # def enable_all(self):
    # 	for module in self.modules:
    # 		logger.info('enable module {} {}...'.format(self.modules[module].__class__.__name__, module))
    # 		self.modules[module].enable()
    #
    # def disable_all(self):
    # 	for module in self.modules:
    # 		logger.info('disable module {} {}...'.format(self.modules[module].__class__.__name__, module))
    # 		self.modules[module].disable()
    #
    # def teardown_all(self):
    # 	for module in self.modules:
    # 		logger.info('teardown module {} {}...'.format(self.modules[module].__class__.__name__, module))
    # 		self.modules[module].teardown()
