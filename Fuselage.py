from parapy.geom import *
from parapy.core import *
from math import *

class Fuselage(GeomBase):
#    fuselage_radius         = Input(max(Payload.dimensions_payload))        #maximum dimension of the payload, assuming a circular cross section
#    section_percentages     = Input(10, 30, 100, 100, 50 , 30 , 20 , 10)    #Section radius percentage
#    fuselage_length         = Input(max(Payload.dimensions_payload)*4)


#    n_sections              = 3                                             #Nose, payload section, rear section

    @Attribute
    def payload_section_radius(self):
        return(1.1*sqrt(0.5*self.parent.payload.height**2+0.5*self.parent.payload.width**2))

    @Attribute
    def battery_section_radius(self):
        return(1.1*sqrt(0.5*self.parent.battery.height**2+0.5*self.parent.battery.width**2))

    @Attribute
    def nose_radius(self):
        return(0.2 * self.battery_section_radius)

    @Attribute
    def aft_fuselage_radius(self):
        return(self.payload_section_radius)

    @Attribute
    def tail_radius(self):
        return(0.2*self.payload_section_radius)

    @Attribute
    def nose_length(self):
        return(0.2*self.parent.battery.length)

    @Attribute
    def aft_fuselage_length(self):
        return(self.parent.battery.length+self.parent.payload.length*1.2)

    @Attribute
    def tail_length(self):
        return(0.2*self.aft_fuselage_length)
    @Input
    def section_radii(self):
       return[self.nose_radius, self.battery_section_radius, self.payload_section_radius, self.aft_fuselage_radius,
              self.tail_radius]

    @Input
    def section_lengths(self):
        return[self.nose_length, self.parent.battery.length, self.parent.payload.length, self.aft_fuselage_length, self.tail_length]

 #   @Attribute
 #   def section_radius(self):
 #       """section radius multiplied by the radius distribution
  #      through the length. Note that the numbers are percentages.
#
 #       :rtype: collections.Sequence[float]
 #       """
 #       return [i * self.fu_radius / 100. for i in self.fu_sections]

#    @Attribute
#    def section_length(self):
#        """section length is determined by dividing the fuselage
 #       length by the number of fuselage sections.
#
 #       :rtype: float
  #      """
 #       return self.fuselage_length / (len(self.section_percentages) - 1)

    @Attribute
    def profiles(self):
        """Used by the superclass LoftedSolid. It could be removed if the
        @Part profile_set would be renamed "profiles" and LoftedSolid
        specified as superclass for Fuselage
        """
        return self.profile_set  # collect the elements of the sequence profile_set

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
                sum(self.section_lengths[:child.index])
            )
        )

    @Part
    def fuselage_lofted(self):
        """This part is redundant as far as LoftedSolid is a Fuselage's
        superclass.
        """
        return LoftedSolid(
            profiles=self.profile_set,
            color="red",
            mesh_deflection=0.0001,
            hidden=False
        )

    @Part
    def fuselage_lofted_ruled(self):
        """This part is redundant as far as LoftedSolid is a Fuselage's
        superclass.
        """
        return LoftedSolid(
            profiles=self.profile_set,
            color="green",
            ruled=True,  # by default this is set to False
            mesh_deflection=0.0001,
            hidden=False
        )

    @Part
    def fuselage_lofted_surf(self):
        """This part is redundant as far as LoftedSurface is a Fuselage's
        superclass
        """
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
