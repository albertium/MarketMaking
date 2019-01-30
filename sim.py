from collections import Counter
import time
import pickle
from pathlib import Path
import dateutil.parser as dp
from datetime import datetime
import const
import market


class Simulator:
    def __init__(self, ticker, date):
        # ------ set up containers ------
        self.queue = []
        self.book = market.OrderBook()

        # ------ parse or retrieve message data ------
        file_name = f'{ticker}_{datetime.strftime(dp.parse(date), "%Y%m%d")}'
        raw_file = file_name + '.csv'
        parsed_file = Path('data') / (file_name + '.pkl')

        start_time = time.time()
        if parsed_file.exists():
            with open(parsed_file, 'rb') as f:
                self.queue = pickle.load(f)
        else:
            self.load_raw_data(Path('data') / raw_file)
            with open(parsed_file, 'wb') as f:
                pickle.dump(self.queue, f)

        # ------ print statistics -----
        print(f'Initialization takes {time.time() - start_time: .2f}s')
        print(f'Total {len(self.queue)} events')
        counts = Counter([x.type for x in self.queue])
        keys = [const.Event.ADD, const.Event.EXECUTE, const.Event.CANCEL, const.Event.DELETE, const.Event.UPDATE]
        for k in keys:
            formatted = f'{counts[k]: ,}'
            print(f'{k.name: <8} {formatted: >9}')

    def load_raw_data(self, path):
        with open(path, 'r') as f:
            msgs = f.readlines()
            for msg in msgs:
                msg = msg.split(',')
                timestamp = int(msg[1])
                ref = int(msg[2])

                if msg[0] == 'A':
                    order = market.LimitOrder(timestamp, ref, const.Side(msg[3]), int(msg[4]), int(msg[5]))
                elif msg[0] == 'E':
                    order = market.MarketOrder(timestamp, const.Side(msg[3]), int(msg[4]), ref)
                elif msg[0] == 'X':
                    order = market.CancelOrder(timestamp, ref, int(msg[3]))
                elif msg[0] == 'D':
                    order = market.DeleteOrder(timestamp, ref)
                elif msg[0] == 'U':
                    order = market.UpdateOrder(timestamp, ref, int(msg[3]), int(msg[4]), int(msg[5]))
                else:
                    raise ValueError('Unknown order type')
                self.queue.append(order)

    def run_simulation(self):
        for event in self.queue:
            if event.type == const.Event.ADD:
                self.book.add_limit_order(event)
            elif event.type == const.Event.EXECUTE:
                self.book.execute_market_order(event)
            elif event.type == const.Event.CANCEL:
                self.book.cancel_order(event)
            elif event.type == const.Event.DELETE:
                self.book.delete_order(event)
            elif event.type ==  const.Event.UPDATE:
                self.book.modify_order(event)

        print('\n====== Simulation Summary ======')
        print(f'Bid Order Book: {len(self.book.bid_book.levels)} orders')
        print(f'Ask Order Book: {len(self.book.ask_book.levels)} orders')
        print(f'Pool:           {len(self.book.pool)} orders')
