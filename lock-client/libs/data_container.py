class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


# #Python2
# class MyClass(BaseClass):
# 	 __metaclass__ = Singleton

# Python3


class DataContainer(metaclass=Singleton):
    """Singleton data_container to access data objects throughout your whole application."""

    pass


data_container = DataContainer()
