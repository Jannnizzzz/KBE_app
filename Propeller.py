
from parapy.core import Base, Input, Attribute, Part

class Propeller(Base):
    propeller = Input()
    thrust_op = Input()
    velocity_op = Input()

    @Input
    def prop_characteristics(self):
        import matlab.engine
        eng = matlab.engine.start_mtlab()
        characteristics, rpm = eng.importPropData('P'+self.propeller+'.dat', nargout=(0, 1))
        return characteristics, rpm

    @Attribute
    def rpm_op(self):
        return 7000

    @Attribute
    def torque_op(self):
        return .0166 * self.thrust_op