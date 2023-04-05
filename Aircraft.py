
from parapy.core import Base, Input, Attribute, Part
from Wing import Wing
from Battery import Battery
from Engine import Engine

class Aircraft(Base):
    endurance = Input()
    endurance_mode = Input()
    wing_airfoil = Input()
    propeller = Input()
    materials = Input()
    velocity = Input(100)
    num_engines = Input(2)
    max_dimensions = Input(3)

    @Attribute
    def total_weight(self):
        return self.battery.weight

    @Part
    def battery(self):
        return Battery(capacity=5000,
                       voltage=25)

    @Part
    def wing(self):
        return Wing()

    #@Part
    #def tail(self):
    #    return Tail()

    @Part
    def engines(self):
        return Engine(quantify=self.num_engines,
                      prop_diameter=1,
                      prop_inclination=1,
                      velocity_op=self.velocity,
                      thrust_op=1)

    #@Part
    #def payload(self):
    #    return Payload()

    #@Part
    #def fuselage(self):
    #    return Fuselage()

if __name__ == '__main__':
    obj = Aircraft(endurance=2,
                   endurance_mode='h',
                   wing_airfoil='NACA4206',
                   propeller='7x7',
                   materials='wood')

    from parapy.gui import display

    display(obj)