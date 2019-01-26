
import bisect
import abc
import const


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

    def get_top_order(self):
        return next(iter(self.orders.values()))

    def add_order(self, order):
        self.num_order += 1
        self.shares += order.shares
        self.orders[order.id] = order

    def match_top_order(self, shares):
        """
        :return: remaining shares, fully executed top order id
        """
        top_order = self.get_top_order()  # type: Order
        if top_order.shares > shares:
            top_order.shares -= shares
            self.shares -= shares
            return 0, None
        else:
            self.remove_order(top_order.id)
            return shares - top_order.shares, top_order.id

    def remove_order(self, order_id):
        self.num_order -= 1
        self.shares -= self.orders[order_id].shares
        del self.orders[order_id]


class Book(abc.ABC):
    def __init__(self, default_level):
        self.prices = []
        self.levels = {}
        self.default_level = default_level  # default price level when the book is empty

    def get_quote(self):
        return self.prices[0] if self.prices else self.default_level

    def get_top_level(self) -> Level:
        return self.levels[self.prices[0]]

    def ensure_level(self, price) -> Level:
        """
        get level from price. If not exists, create one
        """
        level = self.levels.get(price, None)
        if level is None:
            self.add_price(price)
            level = Level()
            self.levels[price] = level
        return level

    def add_order(self, order: Order):
        level = self.ensure_level(order.price)
        level.add_order(order)

    def match_shares(self, remaining_shares):
        # TODO: add check if run the whole book?
        fully_executed = []
        while remaining_shares > 0:
            level = self.get_top_level()
            remaining_shares, order_id = level.match_top_order(remaining_shares)
            fully_executed.append(order_id)

            if level.shares == 0:
                self.remove_top_level()

        return fully_executed

    def remove_top_level(self):
        del self.levels[self.prices[0]]
        self.prices.pop(0)  # TODO: replace with something like deque

    @abc.abstractmethod
    def add_price(self, price):
        pass


class AskBook(Book):
    def __init__(self):
        super(AskBook, self).__init__(1E10)

    def add_price(self, price):
        bisect.insort(self.prices, price)  # TODO: is there better data structure for this?


class BidBook(Book):
    def __init__(self):
        super(BidBook, self).__init__(0)

    def add_price(self, price):
        # TODO: reverse sort
        pass


class OrderBook:
    def __init__(self):
        self.bid_book = BidBook()
        self.ask_book = AskBook()
        self.pool = {}  # to store existing orders

    def add_order(self, order: Order):
        if order.side == const.Side.BID:
            if order.price < self.ask_book.get_quote():
                self.add_order_to_book(order, self.bid_book)
            else:
                self.match_order_in_book(order, self.ask_book)
        else:
            if order.price > self.bid_book.get_quote():
                self.add_order_to_book(order, self.ask_book)
            else:
                self.match_order_in_book(order, self.bid_book)

    def add_order_to_book(self, order: Order, book: Book):
        book.add_order(order)
        self.pool[order.id] = book

    def match_order_in_book(self, order, book: Book):
        # TODO: assuming the order will run the book
        while order.shares > 0:
            level = book.get_top_level()
            limit_order = self.pool[level.get_top_order_id()]  # type: Order
            if limit_order.shares > order.shares:
                limit_order.shares -= order.shares
                level.shares -= order.shares
                order.shares = 0
            else:
                level.shares -= limit_order.shares
                order.shares -= limit_order.shares
                level.remove_order(limit_order.id)
                del self.pool[limit_order.id]

                if level.shares == 0:
                    book.remove_top_level()

    def cancel_order(self, order_id):
        order = self.pool[order_id]
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
