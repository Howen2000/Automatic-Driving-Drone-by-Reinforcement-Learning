from flight_controller import FlightController
from drone import Drone
from typing import Tuple
import numpy as np
import random
import pandas as pd


class CustomController(FlightController):

    def __init__(self, coordin=None):

        coordin.x = 72
        coordin.y = 48

        pass

    def train(self):
        pass

    def get_thrusts(self, drone: Drone) -> Tuple[float, float]:
        target_point = drone.get_next_target()
        drone_position = drone.x, drone.y

        lr = 0.1
        gamma = 0.99

        up = 0.6, 0.6
        down = 0.4, 0.4
        left = 0.5, 0.55
        right = 0.55, 0.5
        stationary = 0.5, 0.5

        actions = [up, down, left, right]
        Q_table = np.zeros((25, len(actions)))

        reward = 25000

        if drone_position == target_point:
            reward += 200;

        total_reward = list()

        def dist(x, y):
            return np.sqrt(np.sum((x - y) ** 2))


        dist_a_b = dist(np.asarray(target_point), np.asarray(drone_position))

        print(dist_a_b)

        if dist_a_b > 0.5:
            final_action = actions[3]
        else:
            final_action = random.choice(actions)

        return (final_action)  # Replace this with your custom algorithm

    def load(self):
        pass

    def save(self):
        pass