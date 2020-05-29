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

class Cell(Agent):
    """
    Base Cell class. Each cell has an oxygen level `e` between 0 and 100. Once
    e > 10, the cell has a chance of activating (set with `activation_odds`).

    Each cell loses one oxygen point per turn. Once the oxygen level falls
    under 10, the cell deactivates.
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
                # print(t)

                if t.vegf > 20 and type(t).__name__ == "Empty":
                    roll = r.random()
                    if roll < 0.1:
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
                self.model.grid.scheduler.add(new_cancer)

        # there is chance to mutate and produce vegf
        self.roll_for_vgef()

        if self.vegf_mutation:
            self.vegf = 30
    
        # to propogate unused resources to other cells
        self.step_maintenance()
            
    
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
    Cell that sends out activation oxygen for up to 15 turns
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

        cancer_coords = (math.floor(2), math.floor(height/2))

        ## Rolled into the placement of other cells
        # self.schedule.add(initial_activator)
        # self.grid.place_agent(initial_activator, center_coords)

        # roll a die and place Producer, Consumer or undifferentiated cell
        for x in range(width):
            for y in range(height):
                roll = r.random()
                coords = (x, y)
                if x == width - 1:
                    agent = Capillary(coords, self)
                elif coords == cancer_coords:
                    agent = Cancer(coords, self)
                elif roll <= proportion_normal:
                    agent = Normal(coords, self)
                else:
                    agent = Empty(coords, self)

                self.schedule.add(agent)
                self.grid.place_agent(agent, coords)
                

    def step(self):
        self.schedule.step() # goes through agents in the order of addition