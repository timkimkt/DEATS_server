# ------------- Inputs for MongoDB ------------- #
import time
from datetime import datetime


def create_user_json(user_info, password=None):
    return {
        "acc_active": True,
        "password": password,
        "user_info": user_info,
        "DEATS_tokens": "3",
        "delivery_info": None
    }


def create_user_info_json(email, username, name=None, phone_num=None):
    return {
        "email": email,
        "name": name,
        "username": username,
        "phone_num": phone_num
    }


# don't need active status: indicated by being put in the order status
# don't need user type: all orders are requested by a customer
# need status: delivered, pending, matched, and picked_up to keep track of order and delivery status
def order_delivery_json(customer, pickup_loc, drop_loc, get_code):
    return {
        "customer": customer,
        "deliverer": None,
        "pickup_loc": pickup_loc,
        "drop_loc": drop_loc,
        "GET_code": get_code,
        "order_date": datetime.fromtimestamp(time.time()),
        "order_status": "pending"
    }


# temporarily assume final location and current location are the same
def make_delivery_json(leaving_from, destination):
    return {
        "delivery_info": {
            "leaving_from": leaving_from,
            "destination": destination
        }
    }


def find_order_json():
    return {
        "$and": [
            {"deliverer": None},  # the order should have no deliverer
            {"order_status": {"$ne": "canceled"}}  # and it should not have a canceled status
        ]
    }


def match_order_filter_json(order_id):
    return {
        "_id": order_id,
        "order_status": "pending",
    }


def unmatch_order_filter_json(order_id, user_id):
    return {
        "_id": order_id,
        "$or": [
            {  # A deliverer should be able to unmatch from a delivery only when the order hasn't been cancelled
                "$and": [
                    {"deliverer.user_id": user_id},  # A deliverer should have permission to be able to unmatch
                    {"order_status": {"$ne": "canceled"}}
                ]
            },
            {  # A customer should only be able to unmatch a deliverer when the order is still in a matched state
                "$and": [
                    {"customer.user_id": user_id},  # A customer should have permission to be able to unmatch
                    {"order_status": "matched"}
                ]
            }
        ]
    }


def cancel_order_filter_json(order_id, customer_id):
    return {
        "_id": order_id,
        "customer.user_id": customer_id
    }


def show_orders_input_json(user_id):
    return {
        "customer.user_id": user_id,
    }


def show_deliveries_input_json(user_id):
    return {
        "deliverer.user_id": user_id,
    }


def show_orders_response_json(succeeded, msg, orders):
    return {
        "succeeded": succeeded,
        "msg": msg,
        "orders": orders
    }


def show_deliveries_response_json(succeeded, msg, deliveries):
    return {
        "succeeded": succeeded,
        "msg": msg,
        "deliveries": deliveries
    }


def match_unmatch_customer_json(deliverer=None, order_status="matched"):
    return {
        "deliverer": deliverer,
        "order_status": order_status
    }


# ------------- JSON responses ------------- #
def login_response_json(succeeded, msg, user_id, user_info, acc_active):
    user = {
        "user_id": user_id,
        "acc_active": acc_active,
        "user_info": user_info
    } if user_id else None

    return {
        "succeeded": succeeded,
        "msg": msg,
        "user": user
    }


def sso_login_response_json(succeeded, msg, user_id, acc_active, name, username,
                            net_id_email, phone_num, is_new_login, authentication_date):
    return {
        "succeeded": succeeded,
        "msg": msg,
        "is_new_login": is_new_login,
        "authentication_date": authentication_date,
        "user": {
            "user_id": user_id,
            "acc_active": acc_active,
            "user_info": {
                "email": net_id_email,
                "name": name,
                "username": username,
                "DEATS_tokens": "3",
                "phone_num": phone_num
            }
        }
    }


def create_acc_response_json(succeeded, msg, user_id=None, username=None, acc_active=None):
    user = {
        "user_id": user_id,
        "user_info": {
            "username": username
        },
        "acc_active": acc_active,
        "DEATS_tokens": "3"
    } if user_id else None

    return {
        "succeeded": succeeded,
        "msg": msg,
        "user": user
    }


def request_denied_json_response(msg):
    return {
        "succeeded": False,
        "msg": msg
    }


def login_request_response_json():
    return {
        "succeeded": False,
        "login": True
    }


def order_delivery_response_json(succeeded, msg, order_id):
    return {
        "succeeded": succeeded,
        "msg": msg,
        "order": {
            "order_id": order_id
        }
    }


def order_json(order_id, pickup_loc, drop_loc):
    return {
        "order": {
            "order_id": order_id,
            "pickup_loc": pickup_loc,
            "drop_loc": drop_loc
        }
    }


def customer_and_order_json(customer, order):
    return {
        "customer": customer,
        "order": order
    }


def start_delivery_response_json(unmatched_users):
    return {
        "succeeded": True,
        "msg": "The request was successful",
        "unmatched_users": unmatched_users
    }


def get_my_deliverer_response(succeeded, msg, deliverer):
    return {
        "succeeded": succeeded,
        "msg": msg,
        "deliverer": deliverer
    }


def make_get_order_status_response(succeeded, msg, order_status):
    return {
        "succeeded": succeeded,
        "msg": msg,
        "order": order_status
    }


def match_response_json(succeeded, msg, customer):
    return {
        "succeeded": succeeded,
        "msg": msg,
        "matched_customer": customer
    }


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


def validation_errors_json(validation_errors):
    return {
        "succeeded": False,
        "msg": "The request was aborted due to data validation failures",
        "data_validation_errors": validation_errors
    }
