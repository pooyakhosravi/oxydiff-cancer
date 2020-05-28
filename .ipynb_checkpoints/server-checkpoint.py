from mesa.visualization.modules import CanvasGrid
from mesa.visualization.ModularVisualization import ModularServer
import cell as c

def cell_portrayal(cell):
    if type(cell).__name__ == "Producer":
        cell_color = "red"
    elif type(cell).__name__ == "Consumer":
        cell_color = "green"
    else:
        cell_color = "grey"

    portrayal = {"Shape": "circle",
                 "Color": cell_color,
                 # "Filled": str(cell.activated),
                 "Filled": "false",
                 "Layer": 0,
                 "r": max(0.1, cell.energy / 100)}
    return portrayal

width = 50
height = 50

grid = CanvasGrid(cell_portrayal, width, height, 600, 600)
server = ModularServer(c.PetriDish, [grid], "Simple cell activation model",
                       {
                           "width": width, "height": height
                       })
