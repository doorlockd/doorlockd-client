import inspect
import logging

logger = logging.getLogger(__name__)


class IoPortsShelf(dict):
    """
    Dict class for temporary storing io_ports. use set(key, io_port) and get(key) only once to set and get io_ports.
    stored value is either the io_port or False if the port is already taken by someone else.

    # example:
    io_ports = IoPortsShelf()
    # after initialising and IOPort place them on the shelf:
    io_ports['2nd_light_bulb'] = io_port_pin_15

    # somewhere els in your application:
    my_light_bulb = io_ports['2nd_light_bulb']

    """

    def __setitem__(self, key, io_port):
        logger.debug(
            f"setitem io_port '{key}' on IoPortsShelf by '{inspect.currentframe().f_back.f_code.co_qualname}'"
        )
        logger.debug(
            f"setitem io_port '{key}' on IoPortsShelf by '{inspect.stack()[1][1:3]}'"
        )

        if key in self.__dict__:
            raise Exception(f"Duplicate io_port '{key}' on IoPortsShelf.")

        self.__dict__[key] = io_port

    def __getitem__(self, key):
        logger.debug(
            f"getitem io_port '{key}' on IoPortsShelf by '{inspect.currentframe().f_back.f_code.co_qualname}'"
        )
        logger.debug(
            f"getitem io_port '{key}' on IoPortsShelf by '{inspect.stack()[1][1:3]}'"
        )

        if key not in self.__dict__:
            raise Exception(f"io_port '{key}' not found on IoPortsShelf.")

        if self.__dict__[key] is False:
            raise Exception(f"io_port '{key}' already taken from IoPortsShelf.")

        # get io_port and replace it with False
        io_port = self.__dict__[key]
        self.__dict__[key] = False
        return io_port
