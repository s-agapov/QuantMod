import pandas as pd
import importlib
from glob import glob

from robot_12 import *


def get_robot(robot_name, params):
    module  = importlib.import_module('TA_robots_01')
    cl = getattr(module, robot_name)
    robot = cl(*params)
    return robot


running = True

while running:
    state_files = glob("States/*")
    for full_fn in state_files:
        df = pd.read_csv(full_fn)
        #Start
        xx = df[df['state'] == -1]
        st_index = xx.index
        if xx.shape[0] > 0:
            new_robots = []
            for ind, row in xx.iterrows():
                params = [row[x] for x in ['p1', 'p2', 'p3', 'p4', 'p5'] if row[x] > 0]
                robot_kernel = get_robot(row['robot'], params)
                robot = Robot(row['market'], row['tf'],  robot_kernel, row['contract'])
                robot.market_position = row['MP']
                robot.contract = row['contract']
                robot.open_position = row['OP']
                robot.num_shares = row['num_shares']
                new_robots.append(robot)

            df.loc[(df['state'] == -1), 'state'] = 0
            df.to_csv(full_fn, index = False)

            for r in new_robots:
                time.sleep(1)
                r.start()
    time.sleep(5)