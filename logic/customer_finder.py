from bson.objectid import ObjectId

from logic.customer import Customer
from logic.deliverer import Deliverer
from math import sqrt
from tests.flask.mongo_client_connection import MongoClientConnection
import heapq

db = MongoClientConnection.get_database()


def compute_distance(loc1, loc2):
    return sqrt((loc2['x'] - loc1['x']) ** 2 + (loc2['y'] - loc1['y']) ** 2)


class CustomerFinder:
    def __init__(self, deliverer_loc, customers):
        self.deliverer = Deliverer(coordinates=deliverer_loc)
        self.customers = customers
        self.queue = []

    def sort_customers(self):
        for customer_json in self.customers:
            print("customer: ", customer_json)

            score = self.compute_score(customer_json["pickup_loc"], customer_json["drop_loc"])
            print("score: ", score)
            print("customer's id: ", str(customer_json["_id"]))
            heapq.heappush(self.queue, Customer(customer_json["customer_id"], str(customer_json["_id"]),
                                                customer_json["pickup_loc"], customer_json["drop_loc"],
                                                customer_json["pickup_loc_name"], customer_json["drop_loc_name"], score))

    def get_k_least_score_customers(self, k):
        least_scored_customers = []

        i = 0
        while self.queue and i < k:
            customer = heapq.heappop(self.queue)
            # Not necessary to return emails/phone contacts of customers to deliverers before they match with
            # a customer...adding just in case deliverers want to call customers to find out more details
            # before they match with them
            # Might take them out in the future if they cause privacy issues
            print("this customer", customer.customer_id)
            result = db.users.find_one({"_id": ObjectId(customer.customer_id)},
                                       {"name": 1, "email": 1, "phone_num": 1, "_id": 0})
            result["pickup_loc_name"] = customer.pickup_loc_name
            result["drop_loc_name"] = customer.drop_loc_name
            result["customer_id"] = customer.customer_id
            result["pickup_loc"] = customer.pickup_loc
            result["drop_loc"] = customer.drop_loc
            result["order_id"] = customer.order_id

            least_scored_customers.append(result)
            i += 1

        print("result", least_scored_customers)
        return least_scored_customers

    def compute_score(self, pickup_loc_coordinates, drop_location_coordinates):
        print(pickup_loc_coordinates, drop_location_coordinates)
        a = compute_distance(self.deliverer.coordinates, pickup_loc_coordinates)
        b = compute_distance(pickup_loc_coordinates, drop_location_coordinates)
        c = compute_distance(pickup_loc_coordinates, self.deliverer.coordinates)

        return a + b - c
