
import time
from sim import Simulator
from input import preprocess_data, parse_raw_itch_file

# parse_raw_itch_file('data/S020118-v50.txt', 'data/tmp.csv')
# preprocess_data('data/AAPL_20180201.csv')
start = time.time()
simulator = Simulator('AAPL', '20180201')
simulator.run_simulation()
print(f'{time.time() - start}')
