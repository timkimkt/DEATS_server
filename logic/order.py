class Order:

    # str: restaurant, status
    # Respective objects: customer, deliverer, order
    def __init__(self, customer, restaurant, details, deliverer=None, status="PENDING"):

        # contains x, y coordinate of each restaurant
        self.restaurant = {"COLLIS": [3, 3], "HOP": [5, 5]}

        # Initial information
        self.customer = customer
        self.rest_loc = self.restaurant[restaurant]
        self.details = details                   # food details
        self.deliverer = deliverer

        # Updated during delivery
        self.status = status                 # pending means not yet matched
        self.confirmation_code = None
        self.complete = False

        self.order_status = ["PENDING", "IN_TRANSIT", "PICKING_UP", "DELIVERING", "COMPLETE"]


    # updates the confirmation code
    def update_code(self, code):
        if not self.confirmation_code:
            self.confirmation_code = code

    def update_status(self, msg):
        self.status = msg

    def order_complete(self):
        self.complete = True