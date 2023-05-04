
from parapy.core import Base, Input, Attribute, Part
from parapy.geom import Box
from parapy.geom.generic.positioning import Position, Point, Orientation
import math

class Battery(Base):
    cap = Input()                   # in Ah
    cells = Input()

    capacity_per_cell = Input(2.6)  # in Ah
    voltage_per_cell = Input(4.2)   # in V
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
        return self.voltage_per_cell * self.cells

    @Attribute
    def weight(self):
        return 9.80665 * .044 * self.num_cells

    @Part
    def geometry(self):
        return Box(self.length/1000, self.width/1000, self.height/1000,
                   position=Position(Point(0, 0, 0), Orientation(x='-x', y='y')))
