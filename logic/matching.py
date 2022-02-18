
from deliverer import *
from customer import *

class Matching:
    def __init__(self):



    # for each user
    queue = [ ]

    while queue:
        # (ID, distance)
        res = [[id, distance] ]
        distance = float('inf')

        curr = queue.popleft()

        for delives/customers
            distance = min(distance, distance(dliver, customer))

        res.sort(lambda x: x[1])
        return res


    def distance(deliver, user):
        # a + b - c
        a = user.distance_to_food
        b = distance_btwn_user_and_deliver
        c = deliver.distance_to_food

        return a + b - c