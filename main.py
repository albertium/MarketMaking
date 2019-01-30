
import time
from sim import Simulator
from input import parse_raw_itch_file

# parse_raw_itch_file('AAPL', 'data/S020118-v50.txt', 'data')
start = time.time()
simulator = Simulator('AAPL', '20180201')
simulator.run_simulation()
print(f'{time.time() - start}')
