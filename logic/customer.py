from math import inf
from functools import total_ordering


@total_ordering  # supply all rich comparisons besides the ones provided
class Customer:

    def __init__(self, customer_id, order_id, pickup_loc, drop_loc, pickup_loc_name, drop_address, score):
        self.customer_id = customer_id
        self.order_id = order_id
        self.pickup_loc = pickup_loc  # x, y coordinates (dict object)
        self.drop_loc = drop_loc  # x, y coordinates (dict object)
        self.pickup_loc_name = pickup_loc_name
        self.drop_address = drop_address
        self.score = score
        self.order = None
        self.matched = False

    def __eq__(self, other):
        return self.score == other.score

    def __lt__(self, other):
        return self.score < other.score
