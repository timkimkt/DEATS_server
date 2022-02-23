from math import inf
from functools import total_ordering

@total_ordering # supply all rich comparisons besides the ones provided
class Customer:

    def __init__(self, id, coordinates):
        self.id = id
        self.coordinates = coordinates   # x, y coordinates
        self.score = inf
        self.order = None
        self.matched = False

    def __eq__(self, other):
        return self.score == other.score

    def __lt__(self, other):
        return self.score < other.score

