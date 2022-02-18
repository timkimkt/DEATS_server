class Order:

    def __init__(self, customer_id, deliverer_id, order):
        # Initial information
        self.customer_id = customer_id
        self.deliverer_id = deliverer_id
        self.order = order                   # [restaurant, food]

        # Updated during delivery
        self.complete = False
        self.confirmation_code = None
        self.status = "IN_TRANSIT"                 # delivery status

    # updates the confirmation code
    def update_code(self, code):
        if not self.confirmation_code:
            self.confirmation_code = code

    def update_status(self, msg):
        self.status = msg

    def order_complete(self):
        self.complete = True