
from parapy.core import Base, Input, Attribute, Part

class Wing(Base):
    semi = Input(False)

    @Attribute
    def weight(self):
        return 0#structure(self).weight()

    @Attribute
    def wing_surface_area(self):
        return 0

    @Attribute
    def taper_ratio(self):
        return 0

    @Attribute
    def root_cord(self):
        return 0

    @Attribute
    def cL(self):
        return 0

    @Attribute
    def cD(self):
        return 0

    #@Part
    #def structure(self):
    #    return Structure()