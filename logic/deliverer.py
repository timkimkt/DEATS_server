from order import *
from customer import *

class Deliverer:

    def __init__(self, id, coordinates, order, status=""):
        self.id = id                     # e.g. d1
        self.coordinates = coordinates   # [x coordinate, y coordinate]
        self.order = None                # refer to order class
        self.status = status             # in-transit, picking-up, delivering, delivered
        self.active = False

    # customer struct is passed in
    def accept_order(self, customer):
        self.order = Order(customer_id=customer.id, deliverer_id=self.id, order=customer.request)
        return True # to let the customer know

    def get_location(self):
        # every x seconds, the location of deliverer is updated
        # use gps to get current location
        pass

    def update_status(self):
        # either depending on location or manual update by deliverer
        # we update the delivery status
        # delivery status: "IN_TRANSIT", "PICKING_UP", "DELIVERING", "COMPLETE"
        pass

    def update_active(self):
        if not self.active:
            self.active = True