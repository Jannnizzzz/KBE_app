
from parapy.core import Base, Input, Attribute, Part
from Wing import Wing

class Tail(Base):


    @Part
    def vertical_tail(self):
        return Wing(True)

    @Part
    def horizontal_tail(self):
        return Wing()