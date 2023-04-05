
from parapy.core import Base, Input, Attribute, Part

class Battery(Base):
    capacity = Input()
    voltage = Input()

    @Attribute
    def weight(self):
        return 0

    @Attribute
    def num_cells(self):
        return 0