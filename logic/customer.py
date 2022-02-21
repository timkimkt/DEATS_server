from deliverer import *

class Customer:

    def __init__(self, id, coordinates):
        self.id = id
        self.coordinates = coordinates   # x, y coordinates
        self.order = None
        self.matched = False

