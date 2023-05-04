
from parapy.core import Base, Input, Attribute, Part
from Wing import Wing
from Battery import Battery
from Engine import Engine

class Aircraft(Base):
    endurance = Input()
    endurance_mode = Input()
    airfoil_root = Input()
    airfoil_tip  = Input()
    propeller = Input()
    materials = Input()
    battery_capacity = Input(5)
    velocity = Input(100)
    air_density = Input()
    num_engines = Input(1)

    max_width = Input()
    max_length = Input()
    max_height = Input()

    payload_width   = Input(0.2)            #m
    payload_length  = Input(0.5)            #m
    payload_height  = Input(0.2)            #m
    payload_weight  = Input(2.0)            #Kg

    structural_material = Input('')


    @Input
    def prop_diameter(self):
        split = self.propeller.index('x')
        return int(self.propeller[:split])

    @Input
    def prop_inclination(self):
        split = self.propeller.index('x')
        return int(self.propeller[split+1:])

    @Attribute
    def total_weight(self):
        return self.battery.weight

    @Attribute
    def endurance_time(self):
        current = 0
        for i in range(self.num_engines):
            current += self.engines[i].current
        return self.battery.capacity/current

    @Attribute
    def endurance_range(self):
        return self.velocity*self.endurance_time

    @Attribute
    def check_endurance(self):
        if self.endurance_mode == 'R':
            factor = self.endurance / self.endurance_range
            if factor >= 1:
                self.battery_capacity = factor * self.battery.capacity
        elif self.endurance_mode == 'T':
            factor = self.endurance / self.endurance_time
            if factor >= 1:
                self.battery_capacity = factor * self.battery.capacity
        return True
    @Part
    def battery(self):
        return Battery(cap=self.battery_capacity,
                       cells=4)

    @Part
    def wing(self):
        return Wing()

    #@Part
    #def tail(self):
    #    return Tail()

    @Part
    def engines(self):
        return Engine(quantify=self.num_engines,
                      prop=self.propeller,
                      velocity_op=self.velocity,
                      thrust_op=1,
                      max_voltage=self.battery.voltage)

    @Part
    def payload(self):
        return Payload(width = self.payload_width,
                       length = self.payload_length,
                       height = self.payload_height,
                       weight = self.payload.weight
        )

    #@Part
    #def fuselage(self):
    #    return Fuselage()

if __name__ == '__main__':
    obj = Aircraft(endurance=2,
                   endurance_mode='T',
                   wing_airfoil='NACA4206',
                   propeller='7x7',
                   materials='wood')

    from parapy.gui import display

    display(obj)