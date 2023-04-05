
from parapy.core import Base, Input, Attribute, Part
import math

class Battery(Base):
    cap = Input()                   # in Ah
    capacity_per_cell = Input(2.6)  # in Ah
    cells = Input()

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
