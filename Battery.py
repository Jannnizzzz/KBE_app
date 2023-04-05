
from parapy.core import Base, Input, Attribute, Part
from parapy.geom import Box
import math

class Battery(Base):
    cap = Input()                   # in Ah
    capacity_per_cell = Input(2.6)  # in Ah
    cells = Input()

    cell_diameter = Input(19)       # in mm
    cell_height = Input(65)         # in mm

    @Attribute
    def width(self):
        return self.cell_diameter * self.cells

    @Attribute
    def length(self):
        return self.cell_diameter * self.num_cells/self.cells

    @Attribute
    def height(self):
        return self.cell_height

    @Attribute
    def num_cells(self):
        return self.cells * math.ceil(self.cap / self.capacity_per_cell)

    @Attribute
    def capacity(self):
        return self.num_cells/self.cells * self.capacity_per_cell

    @Attribute
    def voltage(self):
        return 4.2 * self.cells

    @Attribute
    def weight(self):
        return .044 * self.num_cells

    @Part
    def geometry(self):
        return Box(self.width, self.length, self.height)
