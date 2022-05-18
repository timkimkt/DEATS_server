from logic.order import *
from logic.customer import *

class Deliverer:

    def __init__(self, user_id, coordinates, order=None, status="WAITING"):
        self.user_id = user_id
        self.coordinates = coordinates   # [x coordinate, y coordinate]

        self.active = False              # first check if deliverer is active
        self.status = status             # waiting, in-transit, picking-up, delivering, delivered
        self.order = order                # refer to order object assigned once matched
        # pending means the customer requested but not yet accepted by deliverer

    def get_location(self):
        # every x seconds, the location of deliverer is updated
        # use gps to get current location
        pass

    # switch to indicate whether the deliverer is accepting orders
    # sets self.active to true if accpeting
    def active_switch(self):
        if not self.active:
            self.active = True
        else:
            self.active = False
