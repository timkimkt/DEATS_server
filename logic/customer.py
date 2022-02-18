from deliverer import *

class Customer:

    def __init__(self, id, coordinates, request):
        self.id = id
        self.coordinates = coordinates
        self.request = request
        self.matched = False

    def request_order(self):

        if deliverer.accept_order(self):

        self.matched = True
