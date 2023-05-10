from parapy.geom import *
from parapy.core import *
from math import *

class Fuselage(GeomBase):

    @Attribute
    def payload_section_radius(self):   # defined as the sum of the payload height and width to account for rectangular shapes
        return(sqrt(0.5*self.parent.payload.height**2+0.5*self.parent.payload.width**2))

    @Attribute
    def nose_radius(self):          # smaller value to make the nose go smoother, allows for an engine to fit on the nose
        return(0.2 * self.payload_section_radius)

    @Attribute
    def tail_radius(self):          # smaller value to make the tail section go smoother
        return(0.25*self.payload_section_radius)

    @Attribute
    def payload_section_length(self):     # length taken from ADSEE I and made bigger to allow for systems inside and for reaching inside
        return(3*(self.parent.payload.length + self.parent.battery.length))

    @Attribute
    def nose_length(self):  # slenderness value defined by the ADSEE I course
        return(3.5*self.payload_section_radius)

    @Attribute             # slenderness value defined by the ADSEE I course
    def tail_length(self):
        return(7.5*self.payload_section_radius)

    @Input          # list of section radii for profiles
    def section_radii(self):
       return[self.nose_radius, self.payload_section_radius,self.payload_section_radius, self.tail_radius]

    @Input
    def section_lengths(self):      # list of section lengths for profiles
        return[self.nose_length, self.payload_section_length,self.payload_section_length,  self.tail_length]

    @Attribute
    def fuselage_length(self):      # sum of all sections
        return(self.nose_length+self.payload_section_length+self.tail_length)

    @Attribute
    def fuselage_radius(self):      # for reference in other files
        return self.payload_section_radius


    @Attribute
    def profiles(self):
        return self.profile_set  # collect the elements of the sequence profile_set

    @Attribute
    def x_nose(self): # location of nose to allow for fitting of the battery and payload inside of the fuselage at all times
        return self.nose_length+self.parent.battery.length/2 + self.parent.battery.cog.x

    @Part
    def profile_set(self):
        return Circle(
            quantify=len(self.section_radii), color="Black",
            radius=self.section_radii[child.index],
            # fuselage along the X axis, nose in XOY
            position=translate(
                self.position.rotate90('y'),  # circles are in XY plane, thus need rotation
                Vector(1, 0, 0),
                #child.index * self.section_lengths
                self.x_nose-sum(self.section_lengths[:child.index])
            )
        )


    @Part
    def fuselage_lofted_surf(self):
        return LoftedSurface(
            profiles=self.profile_set,
            color="blue",
            mesh_deflection=0.0001,
            hidden=False
        )

if __name__ == '__main__':
    from parapy.gui import display
    obj = Fuselage(label="fuselage" )#, mesh_deflection=0.0001)
    display(obj)
