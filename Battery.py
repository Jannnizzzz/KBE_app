
from parapy.core import Base, Input, Attribute, Part
from parapy.core.validate import IsInstance
from parapy.geom import Box
from parapy.geom.generic.positioning import Position, Point, Orientation
import math
import numpy as np

class Battery(Base):
    cap = Input()                   # in Ah
    cells = Input()

    capacity_per_cell = Input(2.6)  # in Ah
    voltage_per_cell = Input(4.2)   # in V
    cell_diameter = Input(19)       # in mm
    cell_height = Input(65)         # in mm
    cog = Input(Point(0, 0, 0), validator=IsInstance(Point))

    # calculate batteries width based on the payloads width
    @Attribute
    def width(self):
        return self.cell_diameter / 1000 * np.round(self.parent.payload.width / (self.cell_diameter / 1000))

    # fit batteries length based on width and height as well as number of single cells needed
    @Attribute
    def length(self):
        cells_height = np.round(self.parent.payload.height / (self.cell_height / 1000))
        cells_width = np.round(self.parent.payload.width / (self.cell_diameter / 1000))
        cells_length = np.ceil(self.num_cells / (cells_width * cells_height))
        return self.cell_diameter / 1000 * cells_length

    # calculate batteries height based on the payloads height
    @Attribute
    def height(self):
        return self.cell_height / 1000 * np.round(self.parent.payload.height / (self.cell_height / 1000))

    @Attribute
    def num_cells(self):
        return self.cells * math.ceil(self.cap / self.capacity_per_cell)

    @Attribute
    def capacity(self):
        return self.num_cells/self.cells * self.capacity_per_cell

    @Attribute
    def voltage(self):
        return self.voltage_per_cell * self.cells

    @Attribute
    def weight(self):
        return 9.80665 * .044 * self.num_cells

    @Part
    def body(self):
        return Box(self.length, self.width, self.height,
                   centered=True,
                   position=Position(self.cog, Orientation(x='-x', y='y')))
