from parapy.core import Base, Attribute, Input, Part
from parapy.geom.generic.positioning import Point, Position, Orientation
from parapy.geom import Box


class Payload(Base):
    length = Input()
    width = Input()
    height = Input()
    weight = Input()
    cog_x = Input()
    cog_y = Input()
    cog_z = Input()


    @Attribute
    def dimensions_payload(self):
        return[self.width, self.length, self.height]

    @Attribute
    def cog(self):
        return Point(self.cog_x, self.cog_y, self.cog_z)

    @Part
    def body(self):
        return Box(self.length, self.width, self.height,
                   centered=True,
                   position=Position(self.cog, Orientation(x='-x', y='y')))
