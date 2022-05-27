from bson.objectid import ObjectId
from geopy.distance import geodesic

from logic.customer import Customer
from logic.deliverer import Deliverer
from math import sqrt

from tests.flask import database_and_response_jsons
from tests.flask.mongo_client_connection import MongoClientConnection
import heapq

db = MongoClientConnection.get_database()


def compute_distance(loc1, loc2):
    loc1_tuple = (loc1["lat"], loc1["long"])
    loc2_tuple = (loc2["lat"], loc2["long"])
    distance = geodesic(loc1_tuple, loc2_tuple).miles
    print("distance: ", distance, loc1, loc2)
    return distance


class CustomerFinder:
    def __init__(self, deliverer_id, deliverer_loc, orders):
        self.deliverer = Deliverer(deliverer_id, coordinates=deliverer_loc["coordinates"])
        self.orders = orders
        self.queue = []

    def sort_customers(self):
        for order_json in self.orders:
            print("customer id:", order_json["customer"]["user_id"])
            print("deliverer id:", self.deliverer.user_id)
            if order_json["customer"]["user_id"] == self.deliverer.user_id:
                continue

            print("order: ", order_json)

            score = self.compute_score(
                order_json["pickup_loc"]["coordinates"], order_json["drop_loc"]["coordinates"])
            print("score: ", score)
            print("customer: ", str(order_json["customer"]))
            heapq.heappush(
                self.queue,
                Customer(
                    order_json["customer"],
                    str(order_json["_id"]),
                    order_json["pickup_loc"],
                    order_json["drop_loc"],
                    order_json["order_fee"],
                    score))

    def get_k_least_score_customers(self, k):
        least_scored_customers = []

        i = 0
        while self.queue and i < k:
            customer = heapq.heappop(self.queue)
            # Not necessary to return emails/phone contacts of customers to deliverers before they match with
            # a customer...adding just in case deliverers want to call customers to find out more details
            # before they match with them
            # Might take them out in the future if they cause privacy issues
            print("this customer", customer.customer)
            order_json = database_and_response_jsons.order_json(
                customer.order_id, customer.pickup_loc, customer.drop_loc, customer.order_fee)

            customer_and_order_json = database_and_response_jsons.customer_and_order_json(
                customer.customer, order_json["order"])

            least_scored_customers.append(customer_and_order_json)
            i += 1

        print("result", least_scored_customers)
        return least_scored_customers

    def compute_score(self, pickup_loc_coordinates, drop_location_coordinates):
        print(pickup_loc_coordinates, drop_location_coordinates)
        a = compute_distance(self.deliverer.coordinates, pickup_loc_coordinates)
        b = compute_distance(pickup_loc_coordinates, drop_location_coordinates)
        c = compute_distance(pickup_loc_coordinates, self.deliverer.coordinates)

        return a + b - c
