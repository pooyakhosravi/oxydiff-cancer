"""
Activator cells, consumer cells, and neutral cells.

If an activator cell is active, it will activate both consumers and activators
in the vicinity by transferring oxygen to each. If a consumer cell is active,
it will eventually start sending a negative oxygen to its neighbors.

Activation occurs when oxygen > 10. Once activated, the cell has a chance of
deactivation that increases with activation duration.
"""

import random as r
import math
from mesa import Agent
from mesa.model import Model
from mesa.space import SingleGrid
from mesa.time  import BaseScheduler
import random

class Cell(Agent):
    """
    Base Cell class.
    """

    def __init__(self, unique_id, model, activated = False, activation_odds = 0.5):
        super().__init__(unique_id, model)
        self.oxygen = 0
        self.activated = activated
        self.vegf = 0

    def step_maintenance(self):
        self.subtract_oxygen(1)
        targets = list(self.model.grid.neighbor_iter(self.pos, moore = True))

        # the logic here need work
        # how do we decide the oxygen distribution
        # do we look at all neighbors?


        # can move in all directions
        # probability based on differences and diffusion constant
        # oxygen packets can move in any direction
        for t in targets:
            if type(t).__name__ != "Capillary":
                oxy_to_add = abs((self.oxygen - t.oxygen)/2)
                if self.oxygen > oxy_to_add and self.oxygen > t.oxygen:
                    self.subtract_oxygen(oxy_to_add)
                    t.add_oxygen(oxy_to_add)

            vegf_to_add = (self.vegf - t.vegf)/2
            if vegf_to_add > 0:
                self.vegf -= vegf_to_add
                t.vegf += vegf_to_add

        # self.roll_for_deactivation()

    def step(self):
        self.step_maintenance()


    def add_oxygen(self, n):
        if self.oxygen + n < 100:
            self.oxygen += n
        else:
            self.oxygen = 100

    def subtract_oxygen(self, n):
        if self.oxygen - n >= 0:
            self.oxygen -= n
        else:
            self.oxygen = 0


class Capillary(Cell):
    """
    Cell that provides oxygen and nutritions to neighboring cells

    There is a chance that the capillary will expand into a neighboring cell
    if the cell is empty and the amount of VEGF marker is above a certain threshold
    """

    def __init__(self, unique_id, model, activated = True, supply = 100):
        super().__init__(unique_id, model, activated)
        self.supply = supply


    def step(self):
        # self.step_maintenance()
        # send activation oxygen to the neighboring cells if activated
        if self.activated:
            targets = self.model.grid.neighbor_iter(self.pos, moore = True)
            for t in targets:


                # limit blood vessel growth
                # feedback system to limit the growth
                # smaller capillary, less oxygen supply
                # consume vegf
                if t.vegf > 20 and type(t).__name__ == "Empty":
                    roll = r.random()
                    if roll < 0.1:
                        t.vegf = 0
                        coord = t.pos
                        self.model.grid.remove_agent(t)
                        new_cap = Capillary(coord, self.model)
                        self.model.grid.place_agent(new_cap, coord)
                        self.model.grid.scheduler.add(new_cap)

                t.add_oxygen(self.supply)
        self.oxygen = self.supply


class Cancer(Cell):
    """
        Cancer cell that consumes oxygen to produce itself.
        If there is enough nutrition, the cell will duplicate into a random neighboring cell while consuming half of its energy
        There is also a little chance for the cancer cell to produce VEGF if it is oxygen deficient
            - Vascular endothelial growth factor (VEGF) is a signalling protein that promotes the growth of new blood vessels.
    """
    def __init__(self, unique_id, model, activated = True, vegf_mutation = False):
        super().__init__(unique_id, model, activated)
        self.vegf_mutation = vegf_mutation


    def step(self):
        # self.step_maintenance()
        self.subtract_oxygen(20)

        targets = self.model.grid.neighbor_iter(self.pos, moore = True)
        for t in targets:
            roll = r.random()
            if self.oxygen > 30 and type(t).__name__ == "Empty" and roll < 0.3:
                self.subtract_oxygen(20)
                coord = t.pos
                self.model.grid.remove_agent(t)
                new_cancer = Cancer(coord, self.model, vegf_mutation=self.vegf_mutation)
                self.model.grid.place_agent(new_cancer, coord)
                # when replacing an empty cell, make sure to add it to the scheduler
                self.model.grid.scheduler.add(new_cancer)

        # there is chance to mutate and produce vegf
        self.roll_for_vgef()

        if self.vegf_mutation:
            self.vegf = 30

        # to propogate unused resources to other cells
        self.step_maintenance()

        # tumor necrosis
        # remove tumor cells in the middle of cluster

        # wont kill the intial one
        # kill after some


    def roll_for_vgef(self):
        roll = r.random()
        if roll < .01:
            self.vegf_mutation = True

class Normal(Cell):
    """
    Cell consumes some oxygen and send the remaining to other cells
    """
    def step(self):
        self.subtract_oxygen(1)
        self.step_maintenance()


class Empty(Cell):
    """
    Cell that can be replaced
    """

    def step(self):
        if self.pos == None:
            return
        self.step_maintenance()



class PetriDish(Model):
    """
    Main model instance. It assignes one cell in each grid location, selecting
    its type randomly at the time of assignment; it assigns a single activated
    Producer cell in the middle of the grid.
    """

    def __init__(self, width = 20, height = 20, proportion_normal = 0.3):
        self.running = True
        self.schedule = BaseScheduler(self)
        self.grid = SingleGrid(width, height, torus = False)

        self.grid.scheduler = self.schedule

        cancer_x = random.randint(0, width - 1)
        while True:
            cancer_y = cancer_x + random.randint(-5, 5)
            if cancer_y >= 0 and cancer_y < height and cancer_y != cancer_x:
                break

        cancer_coords = (cancer_x, cancer_y)

        ## Rolled into the placement of other cells
        # self.schedule.add(initial_activator)
        # self.grid.place_agent(initial_activator, center_coords)

        # roll a die and place Producer, Consumer or undifferentiated cell
        for x in range(width):
            for y in range(height):
                roll = r.random()
                coords = (x, y)
                if coords[0] == coords[1]:
                    agent = Capillary(coords, self)
                elif coords == cancer_coords:
                    agent = Cancer(coords, self)
                elif roll <= proportion_normal:
                    agent = Normal(coords, self)
                else:
                    agent = Empty(coords, self)

                self.schedule.add(agent)
                self.grid.place_agent(agent, coords)


    # random permuation each time.
    # shuffle
    def step(self):

        # self.schedule = shuffle(self.schedule)
        self.schedule.step() # goes through agents in the order of addition
