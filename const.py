
from enum import Enum


class Side(Enum):
    BUY = 'B'
    SELL = 'S'


class Event(Enum):
    ADD = 'A'  # add order
    EXECUTE = 'E'  # execute order
    CANCEL = 'X'  # cancel order
    DELETE = 'D'  # delete order
    UPDATE = 'U'  # update order
    MESSAGE = 'M'  # message to agent

