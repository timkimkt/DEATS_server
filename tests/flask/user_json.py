# ------------- Inputs for MongoDB ------------- #
import time
from datetime import datetime


def create_user_json(email, name, phone_num, password):
    return {
        "acc_active": True,
        "password": password,
        "user_info": {
            "email": email,
            "name": name,
            "phone_num": phone_num,
        },
        "delivery_info": None
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
        "deliverer_id": None
    }


def match_order_json(order_id):
    return {
        "_id": order_id,
        "order_status": "pending"
    }


def show_orders_input_json(user_id):
    return {
        "customer_id": user_id,
    }


def show_deliveries_input_json(user_id):
    return {
        "deliverer_id": user_id,
    }


def show_orders_response_json(orders):
    return {
        "orders": orders
    }


def show_deliveries_response_json(deliveries):
    return {
        "deliveries": deliveries
    }


def match_unmatch_customer_json(deliverer=None, order_status="matched"):
    return {
        "deliverer": deliverer,
        "order_status": order_status
    }


# ------------- JSON responses ------------- #
def login_response_json(succeeded, msg, user_id, user_info):
    return {
        "succeeded": succeeded,
        "msg": msg,
        "user": {
            "user_id": user_id,
            "user_info": user_info
        }
    }


def sso_login_response_json(succeeded, msg, user_id, name, net_id_email, phone_num, is_new_login, authentication_date):
    return {
        "succeeded": succeeded,
        "msg": msg,
        "is_new_login": is_new_login,
        "authentication_date": authentication_date,
        "user": {
            "user_id": user_id,
            "user_info": {
                    "email": net_id_email,
                    "name": name,
                    "phone_num": phone_num
            }
        }
    }


def create_acc_response_json(succeeded, msg, user_id=None):
    return {
        "succeeded": succeeded,
        "msg": msg,
        "user": {
            "user_id": user_id,
        }
    }


def delete_acc_response_json(succeeded, msg):
    return {
        "succeeded": succeeded,
        "msg": msg,
    }


def account_status_response_json(succeeded, msg):
    return {
        "succeeded": succeeded,
        "msg": msg,
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


def start_delivery_response_json(unmatched_users):
    return {
        "unmatched_users": unmatched_users
    }


def make_get_my_deliverer_response(succeeded, msg, deliverer_info):
    return {
        "succeeded": succeeded,
        "msg": msg,
        "deliverer": {
            "deliverer_info": deliverer_info
        }
    }


def make_get_order_status_response(succeeded, msg, order_status):
    return {
        "succeeded": succeeded,
        "msg": msg,
        "order": {
            "order_status": order_status
        }
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
