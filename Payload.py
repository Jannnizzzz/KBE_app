from parapy.geom import *
from parapy.core import *



class Payload(GeomBase):
    width   = Input()       #m
    length  = Input()       #m
    height  = Input()       #m

    weight  = Input()       #kg

    @Attribute
    def dimensions_payload(self):
        return[self.width, self.length, self.height]

    @Attribute
    def cog_payload(self):
        return[self.parent.payload.cog]