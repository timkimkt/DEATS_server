from math import inf
from functools import total_ordering


@total_ordering  # supply all rich comparisons besides the ones provided
class Customer:

    def __init__(self, customer, order_id, pickup_loc, drop_loc, order_fee, score):
        self.customer = customer
        self.order_id = order_id
        self.pickup_loc = pickup_loc
        self.drop_loc = drop_loc
        self.order_fee = order_fee
        self.score = score
        self.order = None
        self.matched = False

    def __eq__(self, other):
        return self.score == other.score

    def __lt__(self, other):
        return self.score < other.score
