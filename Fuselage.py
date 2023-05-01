from payload import *

class Fuselage(base):
    radius = Input(max(Payload.dimensions_payload))




    n_sections = 3          #Nose, payload section, rear section

    @Attribute
    def payload_section_radius(self):
        return[1.2*radius]


    @Part


