
from parapy.core import Base, Input, Attribute, Part
from parapy.geom import Cylinder
from parapy.geom.generic.positioning import Position, Point, Orientation
from parapy.core.validate import IsInstance
import numpy as np
import os.path



import matlab.engine
from __init__ import MATLAB_ENG
from __init__ import generate_warning

class Propeller(Base):
    prop = Input()
    thrust = Input()
    velocity_op = Input()
    position = Input(validator=IsInstance(Point))

    @Input
    def prop_diameter(self):
        split = self.prop.index('x')
        return int(self.prop[:split]) * 0.0254

    @Input
    def prop_characteristics(self):
        path = 'P'+self.prop+'.dat'
        if os.path.exists('Prop_data/' + path):
            characteristics, rpm = MATLAB_ENG.importPropFile(path, nargout=2)
            characteristics = np.asarray(characteristics)
            rpm = np.asarray(rpm).flatten()
            return characteristics, rpm
        else:
            generate_warning("Propeller not found", "The propeller you chose was not found in the data base.")
            return None

    @Attribute
    def max_thrust(self):
        characteristics, _ = self.prop_characteristics
        return np.nanmax(characteristics[:, 7, :])

    @Attribute
    def max_velocity(self):
        characteristics, _ = self.prop_characteristics
        return np.nanmax(characteristics[:, 0, :])

    @Attribute
    def op_valid(self):
        characteristics, _ = self.prop_characteristics
        if self.velocity_op <= self.max_velocity and self.thrust <= self.max_thrust \
                and abs(self.thrust_op - self.thrust) < 3:
            return True
        else:
            return False

    @Attribute
    def operation_point(self):
        characteristics, rpm = self.prop_characteristics
        diff_velocities = (characteristics[:, 0, :] - self.velocity_op) / self.max_velocity
        diff_thrust = (characteristics[:, 7, :] - self.thrust) / self.max_thrust
        difference = np.abs(diff_velocities) + np.abs(diff_thrust)
        idx = np.unravel_index(np.nanargmin(difference), difference.shape)
        return idx

    @Attribute
    def rpm_op(self):
        _, rpm = self.prop_characteristics
        return rpm[self.operation_point[1]]

    @Attribute
    def torque_op(self):
        characteristics, _ = self.prop_characteristics
        return characteristics[self.operation_point[0], 6, self.operation_point[1]]

    @Attribute
    def thrust_op(self):
        characteristics, _ = self.prop_characteristics
        return characteristics[self.operation_point[0], 7, self.operation_point[1]]

    @Part
    def body(self):
        return Cylinder(self.prop_diameter/2, .01,
                        position=Position(self.position, Orientation(x='y', y='z')),
                        transparency=0.8)
