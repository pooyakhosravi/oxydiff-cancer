"""
Activator cells, consumer cells, and neutral cells.

If an activator cell is active, it will activate both consumers and activators
in the vicinity by transferring energy to each. If a consumer cell is active,
it will eventually start sending a negative energy to its neighbors.

Activation occurs when energy > 10. Once activated, the cell has a chance of
deactivation that increases with activation duration.
"""

import random as r
import math
from mesa import Agent
from mesa.model import Model
from mesa.space import SingleGrid
from mesa.time  import BaseScheduler

class Cell(Agent):
    """
    Base Cell class. Each cell has an energy level `e` between 0 and 100. Once
    e > 10, the cell has a chance of activating (set with `activation_odds`).

    Each cell loses one energy point per turn. Once the energy level falls
    under 10, the cell deactivates.
    """

    def __init__(self, unique_id, model, activated = False, activation_odds = 0.5):
        super().__init__(unique_id, model)

        self.activated = activated
        self.activation_odds = activation_odds
        self.active_turns = 0

        if activated:
            self.energy = 20
        else:
            self.energy = 5

    def step_maintenance(self):
        self.activate()
        self.subtract_energy(1)
        self.roll_for_deactivation()

    def step(self):
        self.step_maintenance()

    def activate(self):
        if self.activated:
            self.active_turns += 1
        if self.energy > 10: # check for object class?
            if r.random() <= self.activation_odds:
                self.activated = True

    def roll_for_deactivation(self):
        if self.activated:
            # roll for survival chance, which decreases with each active turn
            # (using negative binomial)
            pass
        if self.energy <= 10:
            self.activated = False
            self.active_turns = 0

    def add_energy(self, n):
        if self.energy + n < 100:
            self.energy += n
        else:
            self.energy = 100

    def subtract_energy(self, n):
        if self.energy - n >= 0:
            self.energy -= n
        else:
            self.energy = 0

class Producer(Cell):
    """
    Cell that sends out activation energy for up to 15 turns
    """

    # def __init__(self, unique_id, model, activated = False):
    #     super().__init__(unique_id, model, activated)
    #     if not activated:
    #         self.energy = 6

    def step(self):
        self.step_maintenance()

        # send activation energy to the neighboring cells if activated
        if self.activated and self.active_turns <= 15:
            targets = self.model.grid.neighbor_iter(self.pos, moore = True)
            for t in targets:
                # print(t)
                t.add_energy(r.randint(1, 5))

class Consumer(Cell):
    """
    Cell that sends out deactivation energy after 5 turns
    """

    # def __init__(self, unique_id, model, activated = False):
    #     super().__init__(unique_id, model, activated)
    #     self.energy = 5

    def step(self):
        self.step_maintenance()
        # send negative energy to neighboring cells if activated &
        #   has been on for three turns
        if self.activated and self.active_turns > 5:
            targets = self.model.grid.neighbor_iter(self.pos, moore = True)
            for t in targets:
                t.subtract_energy(r.randint(1, 5))

class PetriDish(Model):
    """
    Main model instance. It assignes one cell in each grid location, selecting
    its type randomly at the time of assignment; it assigns a single activated
    Producer cell in the middle of the grid.
    """

    def __init__(self, width = 150, height = 150, proportion_producers = 0.5, proportion_consumers = 0.3):
        self.running = True
        self.schedule = BaseScheduler(self)
        self.grid = SingleGrid(width, height, torus = False)

        initial_activator = Producer("Initial activator", self, activated = True)
        center_coords = (math.floor(width / 2), math.floor(height - 1))

        ## Rolled into the placement of other cells
        # self.schedule.add(initial_activator)
        # self.grid.place_agent(initial_activator, center_coords)

        # roll a die and place Producer, Consumer or undifferentiated cell
        for x in range(width):
            for y in range(height):
                roll = r.random()
                coords = (x, y)

                if coords == center_coords:
                    agent = initial_activator
                elif roll <= proportion_producers:
                    agent = Producer(coords, self)
                elif roll <= proportion_producers + proportion_consumers:
                    agent = Consumer(coords, self)
                else:
                    agent = Cell(coords, self)

                self.schedule.add(agent)
                self.grid.place_agent(agent, coords)

    def step(self):
        self.schedule.step() # goes through agents in the order of addition
