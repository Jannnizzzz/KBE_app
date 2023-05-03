
from parapy.core import Base, Input, Attribute, Part
import numpy as np


import matlab.engine
from __init__ import MATLAB_ENG

class Propeller(Base):
    propeller = Input()
    thrust_op = Input()
    velocity_op = Input()


    @Input
    def prop_characteristics(self):
        characteristics, rpm = MATLAB_ENG.importPropFile('P'+self.propeller+'.dat', nargout=2)
        characteristics = np.asarray(characteristics)
        rpm = np.asarray(rpm).flatten()
        return characteristics, rpm

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
        if self.velocity_op <= self.max_velocity and self.thrust_op <= self.max_thrust:
            return True
        else:
            return False

    @Attribute
    def operation_point(self):
        characteristics, rpm = self.prop_characteristics
        diff_velocities = (characteristics[:, 0, :] - self.velocity_op) / self.max_velocity
        diff_thrust = (characteristics[:, 7, :] - self.thrust_op) / self.max_thrust
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