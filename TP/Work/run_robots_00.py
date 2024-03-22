import pandas as pd
import importlib
from glob import glob

from robot_11w import *


def get_robot(robot_name, params):
    module  = importlib.import_module('TA_robots_01')
    cl = getattr(module, robot_name)
    robot = cl(*params)
    return robot


running = True

while running:
    state_files = glob("States/*")
    df = pd.read_csv('states.txt')
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
            robot.num_shares = row['contract']
            robot.open_position = row['OP']
            new_robots.append(robot)

        df.loc[(df['state'] == -1), 'state'] = 0
        df.to_csv('states.txt', index = False)

        for r in new_robots:
            time.sleep(1)
            r.start()
    time.sleep(5)