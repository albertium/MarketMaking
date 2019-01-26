
import bisect


class Order:
    def __init__(self, oid, side, price, shares, time):
        self.id = oid
        self.side = side
        self.price = price
        self.shares = shares
        self.time = time


class Level:
    def __init__(self):
        self.num_order = 0
        self.shares = 0
        self.orders = {}  # store Order object, preserving time priority


class Book:
    def __init__(self):
        self.prices = []
        self.levels = {}
        self.pool = {}  # to store existing orders

    def add_order(self, order: Order):
        """
        For adding same side order
        """
        level = self.levels.get(order.price, None)  # type: Level
        if level is None:
            level = Level()
            bisect.insort(self.prices, order.price)  # TODO: is there better data structure for this?
            self.levels[order.price] = level

        level.num_order += 1
        level.shares += order.shares
        level.orders[order.id] = None  # add order id
        self.pool[order.id] = order

    def match_order(self, order):
        """
        For matching opposite side order
        """

        # TODO: assuming the order will run the book
        while order.shares > 0:
            level = self.levels[self.prices[0]]  # type: Level
            limit_order = self.pool[next(iter(level.orders))]  # type: Order
            if limit_order.shares > order.shares:
                limit_order.shares -= order.shares
                level.shares -= order.shares
                order.shares = 0
            else:
                level.shares -= limit_order.shares
                order.shares -= limit_order.shares
                del level.orders[limit_order.id]
                del self.pool[limit_order.id]

                if level.shares == 0:
                    del self.levels[self.prices[0]]
                    self.prices.pop(0)  # TODO: replace with something like deque

    def cancel_order(self, oid):
        order = self.pool[oid]
        level = self.levels[order.price]
        level.num_order -= 1
        level.shares -= order.shares
        del level.orders[order.id]
        del self.pool[oid]

    def modify_order(self, order: Order):
        limit_order = self.pool[order.id]  # type: Order
        level = self.levels[limit_order.price]
        delta = order.shares - limit_order.shares
        level.shares += delta
        limit_order.shares = order.shares


class AskBook(Book):
    def __init__(self):
        super().__init__()




class BidBook(Book):
    pass
