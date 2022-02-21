from collections import deque
from deliverer import Deliverer
from customer import Customer
from math import *

class Match:
    def __init__(self):
        self.queue = deque()
        self.active_deliverer = [ ]

    # process n number of requests
    # assumes that active deliverer has been updated
    def process_queue(self, n):

        if not self.queue:
            print("From match.py: Queue empty")

        # process either min of requests, available deliver, or n
        n = min(len(self.queue),len(self.active_deliverer), n)

        for _ in range(n):
            customer = self.queue.popleft()
            min_dist = float('inf')
            deliverer_cand = None

            for deliverer in self.active_deliverer:
                curr_dist = self.calc_distance(customer, deliverer)
                if curr_dist < min_dist:
                    min_dist = curr_dist
                    deliverer_cand = deliverer

            if deliverer_cand:
                # update customer info
                customer.order.deliverer = deliverer_cand
                customer.matched = True

                # update deliverer info
                deliverer_cand.order = customer.order
                deliverer_cand.status = "IN_TRANSIT"

                print("From match.py: ",customer.id, "matched with", deliverer_cand.id)

            else:
                print("From match.py: ",customer.id, " failed to match with active deliverer")

    # updates list of active deliverers
    def update_active_deliverer(self, db):
        # reset list
        self.active_deliverer = [ ]

        for deliverer in db:
            if deliverer.active == True:
                self.active_deliverer.append(deliverer)

    # distance helper
    def dist_helper(self, loc1, loc2):
        # returns Euclidean distance between loc1 and loc2
        return sqrt(abs(loc1[0] - loc2[0]) ** 2 + abs(loc1[1] - loc2[1]) ** 2)

    def calc_distance(self, customer, deliverer):
        # a + b - c

        # customer distance to food
        a = self.dist_helper(customer.coordinates, customer.order.rest_loc)
        # distance between customer and deliverer
        b = self.dist_helper(customer.coordinates, deliverer.coordinates)
        # distance between deliverer and restaurant
        c = self.dist_helper(deliverer.coordinates, customer.order.rest_loc)

        if (a + b - c) <= 0:
            print("From match.py: distance calc error")

        return abs(a + b - c)   # should be greater than zero

