
from datetime import timedelta
import const


def show_time(timestamp):
    return '' if timestamp is None else str(timedelta(microseconds=timestamp / 1000))


class Event:
    def __init__(self, event_type):
        self.type = event_type


class LimitOrder(Event):
    def __init__(self, timestamp, order_id, side, price, shares):
        super(LimitOrder, self).__init__(const.Event.ADD)
        self.timestamp = timestamp
        self.id = order_id
        self.side = side
        self.price = price
        self.shares = shares

    def __str__(self):
        return f'{self.id} {show_time(self.timestamp)} {self.side} {self.price} {self.shares}'


class MarketOrder(Event):
    def __init__(self, timestamp, side, shares, order_id=None):
        """
        empty order id means simulated order
        """
        super(MarketOrder, self).__init__(const.Event.EXECUTE)
        self.timestamp = timestamp
        self.side = side
        self.shares = shares
        self.id = order_id

    def __str__(self):
        return f'{show_time(self.timestamp)} {self.side} {self.shares} [{self.id}]'


class CancelOrder(Event):
    def __init__(self, timestamp, order_id, shares):
        super(CancelOrder, self).__init__(const.Event.CANCEL)
        self.timestamp = timestamp
        self.id = order_id
        self.shares = shares

    def __str__(self):
        return f'{show_time(self.timestamp)} {self.id} {self.shares}'


class DeleteOrder(Event):
    def __init__(self, timestamp, order_id):
        super(DeleteOrder, self).__init__(const.Event.DELETE)
        self.timestamp = timestamp
        self.id = order_id

    def __str__(self):
        return f'{show_time(self.timestamp)} {self.id}'


class UpdateOrder(Event):
    def __init__(self, timestamp, order_id, old_id, price, shares):
        super(UpdateOrder, self).__init__(const.Event.UPDATE)
        self.timestamp = timestamp
        self.id = order_id
        self.old_id = old_id
        self.price = price
        self.shares = shares

    def split_order(self, side: const.Side):
        return DeleteOrder(self.timestamp, self.old_id), \
               LimitOrder(self.timestamp, self.id, side, self.price, self.shares)

    def __str__(self):
        return f'{show_time(self.timestamp)} {self.old_id}->{self.id} {self.price} {self.shares}'
