from logic.customer import Customer
from logic.deliverer import Deliverer 
from math import sqrt
import heapq

def compute_distance(loc1, loc2):
    return sqrt((loc2['x'] - loc1['x'])**2 + (loc2['y'] - loc1['y'])**2)

class CustomerFinder:
    def __init__(self, deliverer_loc, customers):
        self.deliverer = Deliverer(coordinates=deliverer_loc)
        self.customers = customers
        self.queue = []
    
    def sort_customers(self):    
        for customer_json in self.customers:
            print("customer: ", customer_json)
            score = self.compute_score(customer_json["fin_location"], customer_json["res_location"])
            print("score: ", score)
            print("customer's id: ", str(customer_json["_id"]))
            heapq.heappush(self.queue, Customer(str(customer_json["_id"]), score))

    def get_k_least_score_customers(self, k):
        result = []

        i = 0
        while self.queue and i < k:
            result.append(heapq.heappop(self.queue).id)
            i += 1

        print("result", result)
        return result

    def compute_score(self, customer_coordinates, food_coordinates):
        print(customer_coordinates, food_coordinates)
        a = compute_distance(self.deliverer.coordinates, food_coordinates)
        b = compute_distance(customer_coordinates, food_coordinates)
        c = compute_distance(customer_coordinates, self.deliverer.coordinates)

        return a + b - c
    