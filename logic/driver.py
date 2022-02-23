# test driver for the classes
# Notes:
# - customer id starts with c, deliverer id starts with d

from customer import Customer
from deliverer import Deliverer
from order import Order
from match import Match

# initialize match queue
match1 = Match()

# create customer
customer1 = Customer(id="c1", coordinates=(0, 0))
# create order by customer 1
order1 = Order(customer1, restaurant="HOP", details="Billybob")
# store order in customer
customer1.order = order1

# TO DO: get all deliverers from database
# db_deliverer = database.request()
deliverer1 = Deliverer(id="d1", coordinates=(1, 1))
deliverer1.active_switch()
db_deliverer = [deliverer1]                # pass in one active deliverer for testing
match1.update_active_deliverer(db_deliverer)

match1.queue.append(customer1)
match1.process_queue(n=1)      # n indicates number of requests to process

# print statements to demonstrate results of matching
print("Customer order:", customer1.order.details, "| Match status:", customer1.matched)
print("Deliverer order:", deliverer1.order.details, "| Status:", deliverer1.status)


