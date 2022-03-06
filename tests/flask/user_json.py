# ------------- Inputs for MongoDB ------------- #
import time
from datetime import datetime


def create_user_json(email, password, name=None, phone_num=None):
    return {
        "email": email,
        "name": name,
        "password": password,
        "phone_num": phone_num,
        "user_type": None,
        "active": False,
        "final_des": {
            "x": None,
            "y": None
        },
        "res_location": {
            "x": None,
            "y": None
        }
    }


# don't need active status: indicated by being put in the order status
# don't need user type: all orders are requested by a customer
# need status: C (completed), W (waiting), M (matched), F (food picked up) to keep track of order and delivery status
def order_delivery_json(customer_id, pickup_loc, drop_loc, pickup_loc_name, drop_address):
    return {
        "customer_id": customer_id,
        "deliverer_id": None,
        "pickup_loc": pickup_loc,
        "drop_loc": drop_loc,
        "pickup_loc_name": pickup_loc_name,
        "drop_address": drop_address,
        "order_date": datetime.fromtimestamp(time.time()),
        "order_status": "W"
    }


# temporarily assume final location and current location are the same
def make_delivery_json(fin_location):
    return {
        "user_type": 'D',
        "active": True,
        "final_des": fin_location
    }


def find_order_json():
    return {
        "deliverer_id": None
    }


def match_order_json(customer_id):
    return {
        "customer_id": customer_id,
        "order_status": "W"
    }


def show_orders_json(user_id):
    return {
        "customer_id": user_id,
    }


def show_deliveries_json(user_id):
    return {
        "delivery_id": user_id,
    }


def show_orders_response_json(orders):
    return {
        "orders": orders
    }


def show_deliveries_response_json(deliveries):
    return {
        "deliveries": deliveries
    }


def match_customer_json(deliverer_id=None, order_status="M"):
    return {
        "deliverer_id": deliverer_id,
        "order_status": order_status
    }


# ------------- JSON responses ------------- #
def login_response_json(succeeded, msg, id, name, phone_num):
    return {
        "succeeded": succeeded,
        "msg": msg,
        "id": id,
        "name": name,
        "phone_num": phone_num
    }


def create_acc_response_json(succeeded, msg, user_id=None):
    return {
        "succeeded": succeeded,
        "msg": msg,
        "user_id": user_id,
    }


def delete_acc_response_json(succeeded, msg):
    return {
        "succeeded": succeeded,
        "msg": msg,
    }


def order_delivery_response_json(succeeded, order_id):
    return {
        "succeeded": succeeded,
        "order_id": order_id
    }


def start_delivery_response_json(unmatched_users):
    return {
        "unmatched_users": unmatched_users
    }


def make_get_order_status_response(result, msg):
    result["msg"] = msg


def success_response_json(succeeded, msg):
    return {
        "succeeded": succeeded,
        "msg": msg
    }


def show_users_response_json(registered_users):
    return {
        "registered_users": registered_users
    }


def global_count_response_json(global_count):
    return {
        "global count": global_count
    }
