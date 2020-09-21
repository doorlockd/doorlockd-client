# from libs.data_container import data_container
# from app import data_container
from app import data_container as dc


# data_container
# from libs.Solenoid import Solenoid

from libs.UiLeds import UiLeds

l = UiLeds()
l.selftest()