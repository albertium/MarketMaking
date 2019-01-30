
import abc
from sortedcontainers import SortedList
import const
from . import orders


class Level:
    def __init__(self, price):
        self.price = price
        self.num_order = 0
        self.shares = 0
        self.orders = {}  # store Order object, preserving time priority

    def get_top_order(self):
        return next(iter(self.orders.values()))

    def add_order(self, order):
        self.num_order += 1
        self.shares += order.shares
        self.orders[order.id] = order

    def execute_order_shares(self, order: orders.MarketOrder):
        """
        execute against a specific order
        :return remaining shares, executed
        """
        limit_order = self.orders[order.id]
        if limit_order.shares > order.shares:
            self.cancel_order(order)  # this is slightly inefficient
            return False, 0
        else:
            self.remove_order(order.id)
            return True, order.shares - limit_order.shares

    def match_top_order(self, shares):
        """
        :return: remaining shares, fully executed ind, matched order id, executed shares
        """
        top_order = self.get_top_order()  # type: orders.LimitOrder
        if top_order.shares > shares:
            top_order.shares -= shares
            self.shares -= shares
            return 0, False, top_order.id, shares
        else:
            self.remove_order(top_order.id)
            return shares - top_order.shares, True, top_order.id, top_order.shares

    def cancel_order(self, order: (orders.CancelOrder, orders.MarketOrder)):
        self.orders[order.id].shares -= order.shares
        self.shares -= order.shares

    def remove_order(self, order_id):
        self.num_order -= 1
        self.shares -= self.orders[order_id].shares
        del self.orders[order_id]


class Book(abc.ABC):
    def __init__(self, side, default_level, key_func=None):
        self.side = side
        self.prices = SortedList(key=key_func)  # TODO: test against regular list and SortedDict
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
            self.prices.add(price)
            level = Level(price)
            self.levels[price] = level
        return level

    def add_order(self, order: orders.LimitOrder):
        level = self.ensure_level(order.price)
        level.add_order(order)
        return level

    def execute_shares(self, remaining_shares, price=None):
        """
        :return executed limit orders, executions (to be change to quantity only), remaining shares
        """
        # TODO: add check if run the whole book?
        fully_executed = []
        executions = []
        while remaining_shares > 0:
            if self.is_outside_book(price):
                break

            level = self.get_top_level()
            remaining_shares, ind, order_id, executed_shares = level.match_top_order(remaining_shares)
            executions.append((order_id, executed_shares))
            if ind:
                fully_executed.append(order_id)

            # TODO: this logic should be under if ind. we should also check for num_order instead
            if level.shares == 0:
                self.remove_top_level()

        return fully_executed, executions, remaining_shares

    def remove_top_level(self):
        del self.levels[self.prices[0]]
        self.prices.pop(0)

    def remove_level(self, level: Level):
        # TODO: need a better data structure to handle this
        del self.levels[level.price]
        self.prices.remove(level.price)  # remove can raise ValueError if not exists

    def get_depth(self):
        output = []
        for price in self.prices:
            output.append((price / 1E4, self.levels[price].shares))
        return output

    @abc.abstractmethod
    def is_outside_book(self, price):
        pass


class BidBook(Book):
    def __init__(self):
        super(BidBook, self).__init__(const.Side.BUY, 0, lambda x: -x)

    def is_outside_book(self, price):
        if price is None:
            return False
        return price > self.get_quote()


class AskBook(Book):
    def __init__(self):
        super(AskBook, self).__init__(const.Side.SELL, 1E10)

    def is_outside_book(self, price):
        if price is None:
            return True
        return price < self.get_quote()


class OrderBook:
    def __init__(self):
        self.bid_book = BidBook()
        self.ask_book = AskBook()
        self.pool = {}  # to store existing orders

    def add_limit_order(self, order: orders.LimitOrder):
        if order.side == const.Side.BUY:
            if order.price < self.ask_book.get_quote():
                self._add_order_to_book(order, self.bid_book)
            else:
                print('======================= cross !!!! =======================')
                order.shares = self._execute_limit_order(order, self.ask_book)
                if order.shares > 0:
                    self._add_order_to_book(order, self.bid_book)
        else:
            if order.price > self.bid_book.get_quote():
                self._add_order_to_book(order, self.ask_book)
            else:
                print('======================= cross !!!! =======================')
                order.shares = self._execute_limit_order(order, self.bid_book)
                if order.shares > 0:
                    self._add_order_to_book(order, self.ask_book)

    def execute_market_order(self, order: orders.MarketOrder):
        """
        this function accepts market orders which may run the book
        """
        book = self.ask_book if order.side == const.Side.BUY else self.bid_book
        limit_book, level = self.pool.get(order.id, (None, None))  # type: (Book, Level)

        # need to execute against the referenced order first because sometimes time priority is not followed
        if limit_book:
            if book != limit_book:
                raise RuntimeError('wrong book!!')
            ind, order.shares = level.execute_order_shares(order)  # get remaining shares
            if ind:
                del self.pool[order.id]

            if level.num_order == 0:
                book.remove_level(level)

        if order.shares > 0:
            print('market order is not fully executed')
            executed, executions, remaining_shares = book.execute_shares(order.shares)
            self._clean_up_limit_order(executed)

    def cancel_order(self, order: orders.CancelOrder):
        """
        order id is the id of the order being cancelled, not the id of the current order
        """
        _, level = self.pool[order.id]  # type: (Book, Level)
        level.cancel_order(order)

    def delete_order(self, order: orders.DeleteOrder):
        book, level = self.pool[order.id]  # type: (Book, Level)
        level.remove_order(order.id)
        if level.num_order == 0:
            book.remove_level(level)
        del self.pool[order.id]

    def modify_order(self, order: orders.UpdateOrder):
        book, _ = self.pool[order.old_id]  # type: (Book, Level)
        delete_order, limit_order = order.split_order(book.side)  # type: (market.DeleteOrder, market.LimitOrder)
        self.delete_order(delete_order)
        self.add_limit_order(limit_order)  # add order will take care of pool keeping

    def _add_order_to_book(self, order: orders.LimitOrder, book: Book):
        level = book.add_order(order)  # type: Level
        self.pool[order.id] = book, level

    def _execute_limit_order(self, order: orders.LimitOrder, book: Book):
        """
        execute limit order that cross the book. limit order may not run the book completely
        """
        executed, executions, remaining_shares = book.execute_shares(order.shares, order.price)
        self._clean_up_limit_order(executed)
        return remaining_shares

    def _clean_up_limit_order(self, executed):
        for order_id in executed:
            del self.pool[order_id]

    def get_depth(self):
        return self.bid_book.get_depth(), self.ask_book.get_depth()
