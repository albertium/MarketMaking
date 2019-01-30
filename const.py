
from enum import Enum


class Side(Enum):
    BUY = 0
    SELL = 1


class Event(Enum):
    ADD = 0  # add order
    EXECUTE = 1  # execute order
    CANCEL = 2  # cancel order
    DELETE = 3  # delete order
    UPDATE = 4  # update order
    MESSAGE = 5  # message to agent


EventTypeMapping = {
    'AA': Event.ADD,
    'AB': Event.ADD,
    'EA': Event.EXECUTE,
    'EB': Event.EXECUTE,
    'X': Event.CANCEL,
    'D': Event.DELETE,
    'U': Event.UPDATE,
}


SideMapping = {
    'AA': Side.SELL,
    'AB': Side.BUY,
    'EA': Side.BUY,
    'EB': Side.SELL,
}
