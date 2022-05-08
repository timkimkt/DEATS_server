import redis
from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from bson import json_util
from cas import CASClient
from werkzeug.utils import redirect
from os import getenv
import tests.flask.database_and_response_jsons as user_json

from bson.objectid import ObjectId
from datetime import timedelta
from flask import Flask, request, session, url_for, jsonify
from flask_session import Session
from logic.customer_finder import CustomerFinder
from tests.flask.helper_functions import validate_password
from tests.flask.mongo_client_connection import MongoClientConnection
from tests.flask.validate_email import validate_email
from flask_apispec import FlaskApiSpec, doc, marshal_with
from webargs.flaskparser import use_args
from tests.flask.schemas import UserIdSchema, CreateAccSchema, UpdateAccSchema, LoginSchema, OrderDelSchema, \
    UpdateOrderSchema, MakeDelSchema, OrderIdSchema, UserIdOrderIdSchema, MatchOrderSchema, CreateAccResponseSchema

db = MongoClientConnection.get_database()
app = Flask(__name__)
g_count = 0

# Secret key for cryptographically signing session cookies (Value is in bytes)
app.secret_key = getenv("SECRET_KEY")

"Load configuration"
SESSION_TYPE = "redis"
SESSION_REDIS = redis.from_url("redis://:p202d128f66a40a4c6898c7dd732e48b222138fa5d8d1061d0de35ae3e1919765@ec2-"
                               "107-21-59-180.compute-1.amazonaws.com:24529")

app.config.from_object(__name__)
Session(app)

# Set up documentation for endpoints
app.config.update({
    'APISPEC_SPEC': APISpec(
        title="DEATS Server API Reference",
        version="2.0.0",
        plugins=[MarshmallowPlugin()],
        openapi_version="3.0.2"
    ),
    'APISPEC_SWAGGER_URL': '/DEATS-server-api-json/',
    'APISPEC_SWAGGER_UI_URL': '/DEATS-server-api-ui/'
})

docs = FlaskApiSpec(app)

cas_client = None


# set up cas client using host url presented at first request
@app.before_first_request
def before_first_request_func():
    global cas_client
    cas_client = CASClient(
        version=3,
        service_url=request.host_url + "sso_login",
        server_url="https://login.dartmouth.edu/cas/"
    )


@app.route('/')
def index():
    return redirect(url_for("sso_login"))


@app.route("/create_acc/", methods=['POST'])
@use_args(CreateAccSchema())
@marshal_with(CreateAccResponseSchema, code=200, description="Response json")
@doc(description="Endpoint for creating an account for a new user", tags=['Account'])
def create_account(args):
    try:
        valid_email = validate_email(args["user_info"]["email"])
        user = db.users.find_one({"user_info": {"email": valid_email.email}})
        print("email_check", user)
        if user:
            msg = "The Dartmouth email provided is taken. Log in instead if it's your account or use a " \
                  "different email address"
            return user_json.create_acc_response_json(False, msg)

        elif args["password"]:
            # strong password creation is a pain, so allow developers to test without password validation
            if not args["test"]:
                validate_password(args["password"])

            args["user_info"]["email"] = valid_email.email
            result = db.users.insert_one(
                user_json.create_user_json(args["user_info"], args["password"]))
            msg = "User deets are now on the server"

            # save user session
            user_id = str(result.inserted_id)
            session["user_id"] = user_id

            # save account active status for easy access later on
            session["acc_active"] = True

            return user_json.create_acc_response_json(True, msg, user_id)

    except ValueError as err:
        return user_json.create_acc_response_json(False, str(err))


@app.route("/update_acc/", methods=['POST'])
@use_args(UpdateAccSchema(), unknown=None)
def update_account(args):
    if not session.get("user_id"):
        msg = "Request denied. This device is not logged into the server yet"
        return user_json.request_denied_json_response(msg)

    succeeded = 0
    for key, value in args.items():
        if key == "password":
            try:
                validate_password(args["password"])

            except ValueError as err:
                return user_json.success_response_json(False, str(err))

        result = db.users.update_one({"_id": ObjectId(args["user_id"])},
                                     {"$set": {key: value}})
        succeeded = max(succeeded, result.modified_count)

    # bulk update message; might do individual messaging in the future
    msg = "The user's account has been updated" if succeeded else "The request was not completed. Nothing new was" \
                                                                  "passed"
    return user_json.success_response_json(bool(succeeded), msg)


@app.route("/delete_acc/", methods=['POST'])
@use_args(UserIdSchema(), unknown=None)
def delete_account(args):
    if not session.get("user_id"):
        msg = "Request denied. This device is not logged into the server yet"
        return user_json.request_denied_json_response(msg)

    result = db.users.delete_one({"_id": ObjectId(args["user_id"])})
    if result.deleted_count:
        msg = "User with id, " + args["user_id"] + ", has been deleted from the server"
        session.pop("user_id", default=None)

    else:
        msg = "Request unsuccessful. No user with id, " + args["user_id"] + ", exists on the server"
    return user_json.delete_acc_response_json(bool(result.deleted_count), msg)


@app.route("/deactivate_acc/", methods=['POST'])
@use_args(UserIdSchema(), unknown=None)
def deactivate_account(args):
    if not session.get("user_id"):
        msg = "Request denied. This device is not logged into the server yet"
        return user_json.request_denied_json_response(msg)

    result = db.users.update_one({"_id": ObjectId(args["user_id"])},
                                 {"$set": {"acc_active": False}}, )

    print("deactivate_acc result:", result.raw_result)
    if not result.matched_count:
        msg = "The account with id, " + args["user_id"] + ", does not exist on the server"

    elif result.modified_count:
        msg = "User with id, " + args["user_id"] + ", has been deactivated on the server"
        session["acc_active"] = False

    else:
        msg = "The account for user with id, " + args["user_id"] + ", is already deactivated"

    return user_json.account_status_response_json(bool(result.modified_count), msg)


@app.route("/reactivate_acc/", methods=['POST'])
@use_args(UserIdSchema(), unknown=None)
def reactivate_account(args):
    if not session.get("user_id"):
        msg = "Request denied. This device is not logged into the server yet"
        return user_json.request_denied_json_response(msg)

    result = db.users.update_one({"_id": ObjectId(args["user_id"])},
                                 {"$set": {"acc_active": True}}, )
    print("reactivate_acc result:", result.raw_result)
    if not result.matched_count:
        msg = "The account with id, " + args["user_id"] + ", does not exist on the server"

    elif result.modified_count:
        msg = "User with id, " + args["user_id"] + ", has been reactivated on the server"
        session["acc_active"] = True

    else:
        msg = "The account for user with id, " + args["user_id"] + ", is already active"

    return user_json.account_status_response_json(bool(result.modified_count), msg)


@app.route("/sso_login/")
def sso_login():
    next = request.args.get('next')
    service_ticket = request.args.get("ticket")

    print("next", next)
    print(("service_ticket", service_ticket))

    # redirect to CAS server for user login if no ticket is found
    if not service_ticket:
        login_url = cas_client.get_login_url()
        print(login_url)
        return redirect(login_url)

    # verify the ticket if it exists
    user, attributes, pgtiou = cas_client.verify_ticket(service_ticket)

    print("user", user)
    print("attributes", attributes)
    print("pgtiou", pgtiou)

    net_id_email = attributes.get("netid") + "@dartmouth.edu"

    if user:
        result_find = db.users.find_one({"user_info": {"email": net_id_email}})

        if result_find:
            msg = "You've logged into DEATS successfully through Dartmouth SSO"
            print(result_find)
            user_id = str(result_find["_id"])
            name = result_find["user_info"]["name"]
            phone_num = result_find["user_info"]["phone_num"]

            # save account active status for easy access later on
            session["acc_active"] = result_find.get("acc_active")

        else:
            name = attributes.get("name")
            result_insert = db.users.insert_one(user_json.create_user_json(net_id_email, name))
            msg = "You've successfully created an account with DEATS through Dartmouth SSO"
            user_id = str(result_insert.inserted_id)
            phone_num = None

            # save account active status for easy access later on
            session["acc_active"] = True

        # save user session
        session["user_id"] = user_id

        return user_json.sso_login_response_json(True,
                                                 msg,
                                                 user_id,
                                                 name,
                                                 net_id_email,
                                                 phone_num,
                                                 attributes.get("isFromNewLogin"),
                                                 attributes.get("authenticationDate")
                                                 )


@app.route("/sso_logout/")
def sso_logout():
    logout_url = cas_client.get_logout_url()
    print("logout_url", logout_url)
    session.pop("user_id", default=None)
    session.pop("acc_active", default=None)

    return redirect(logout_url)


@app.route("/login/", methods=['POST'])
@use_args(LoginSchema(), unknown=None)
def login(args):
    succeeded = False
    user_id = None
    user_info = None

    try:
        valid_email = validate_email(args["user_info"]["email"])
        user = db.users.find_one({"user_info": {"email": valid_email.email}})
        print("email_check", user)
        if not user:
            msg = "The Dartmouth email provided does not exist on the server"

        else:
            user = db.users.find_one({"user_info": {"email": valid_email.email}, "password": args["password"]})
            print("password_check", user)
            if not user:
                msg = "The provided Dartmouth email exists but the password doesn't match what's on the server"

            else:
                print(user)
                succeeded = True
                msg = "Yayy, the user exists!"
                user_id = str(user["_id"])
                user_info = user["user_info"]

                # save user session
                session["user_id"] = user_id

                # save account active status for easy access later on
                session["acc_active"] = user.get("acc_active")

        return user_json.login_response_json(succeeded, msg, user_id, user_info)

    except ValueError as err:
        return user_json.success_response_json(False, str(err))


@app.route("/logout/", methods=['POST'])
@use_args(UserIdSchema(), unknown=None)
def logout(args):
    if session.pop("user_id", default=None) == args["user_id"]:
        succeeded = True
        msg = "The user with id, " + args["user_id"] + ", has been logged out"
    else:
        succeeded = True
        msg = "The request was unsuccessful. The user isn't logged in"

    return user_json.success_response_json(succeeded, msg)


@app.route("/show_users/", methods=['GET'])
def show_users():
    data = request.get_json()
    print("data", data)
    cursor = db.users.find({})
    return user_json.show_users_response_json(str(list(cursor)))


@app.route("/global_count/", methods=['GET'])
def global_count():
    global g_count
    g_count += 1
    return user_json.global_count_response_json(g_count)


@app.route("/order_del/", methods=['POST'])
@use_args(OrderDelSchema(), unknown=None)
def order_delivery(args):
    if not session.get("user_id"):
        msg = "Request denied. This device is not logged into the server yet"
        return user_json.request_denied_json_response(msg)

    if not session.get("acc_active"):
        print(session.get("acc_active"))
        msg = "Request denied. You've deactivated your account. You have to reactivate it before making this request"
        return user_json.request_denied_json_response(msg)

    customer = db.users.find_one({"_id": ObjectId(args["user_id"])}, {"user_info": 1, "_id": 0})
    customer["user_id"] = args["user_id"]

    order_id = db.orders.insert_one(
        user_json.order_delivery_json(customer,
                                      args["order"]["pickup_loc"], args["order"]["drop_loc"],
                                      args["order"]["GET_code"])).inserted_id

    if order_id:
        msg = "The order request has been created successfully"

    else:
        msg = "The request data looks good but the order wasn't created. Try again"

    return user_json.order_delivery_response_json(bool(order_id), msg, str(order_id))


@app.route("/update_order/", methods=['POST'])
@use_args(UpdateOrderSchema(), unknown=None)
def update_order(args):
    if not session.get("user_id"):
        msg = "Request denied. This device is not logged into the server yet"
        return user_json.request_denied_json_response(msg)

    if not session.get("acc_active"):
        print(session.get("acc_active"))
        msg = "Request denied. You've deactivated your account. You have to reactivate it before making this request"
        return user_json.request_denied_json_response(msg)

    succeeded = 0
    order_id = args["order"]["order_id"]
    msg = "The order with id, " + order_id + ", doesn't exist"
    for key, value in args["order"].items():
        if key != "order_id":
            print("key: ", key, " value: ", value)
            result = db.orders.update_one({"_id": ObjectId(order_id)}, {"$set": {key: value}})

            if not result.matched_count:  # return immediately if the order doesn't exist
                return user_json.success_response_json(bool(succeeded), msg)

            succeeded = max(succeeded, result.modified_count)

    msg = "The user's order has been updated" if succeeded else "The request wasn't successful. No new info was " \
                                                                "provided"
    return user_json.success_response_json(bool(succeeded), msg)


@app.route("/make_del/", methods=['POST'])
@use_args(MakeDelSchema(), unknown=None)
def make_delivery(args):
    if not session.get("user_id"):
        msg = "Request denied. This device is not logged into the server yet"
        return user_json.request_denied_json_response(msg)

    if not session.get("acc_active"):
        print(session.get("acc_active"))
        msg = "Request denied. You've deactivated your account. You have to reactivate it before making this request"
        return user_json.request_denied_json_response(msg)

    delivery = args["delivery"]
    result = db.users.update_one({"_id": ObjectId(args["user_id"])},
                                 {"$set": user_json.make_delivery_json(
                                     delivery["leaving_from"], delivery["destination"])}, )
    print("modified: ", result.modified_count, " number of users")

    customer_finder = CustomerFinder(args["user_id"], delivery["destination"],
                                     db.orders.find(user_json.find_order_json()))

    customer_finder.sort_customers()

    return user_json.start_delivery_response_json(
        customer_finder.get_k_least_score_customers(delivery["num_deliveries"]))


@app.route("/my_deliverer/", methods=['POST'])
@use_args(OrderIdSchema(), unknown=None)
def get_my_deliverer(args):
    if not session.get("user_id"):
        msg = "Request denied. This device is not logged into the server yet"
        return user_json.request_denied_json_response(msg)

    if not session.get("acc_active"):
        print(session.get("acc_active"))
        msg = "Request denied. You've deactivated your account. You have to reactivate it before making this request"
        return user_json.request_denied_json_response(msg)

    deliverer_info = db.orders.find_one({"_id": ObjectId(args["order_id"])}, {"deliverer.deliverer_info": 1, "_id": 0})

    if deliverer_info:
        succeeded = True
        msg = "Deliverer found!"

    else:
        succeeded = False
        msg = "No deliverer for this order yet. Check again later"

    return user_json.make_get_my_deliverer_response(succeeded, msg, deliverer_info)


@app.route("/order_status/", methods=['POST'])
@use_args(UserIdOrderIdSchema(), unknown=None)
def get_order_status(args):
    if not session.get("user_id"):
        msg = "Request denied. This device is not logged into the server yet"
        return user_json.request_denied_json_response(msg)

    if not session.get("acc_active"):
        print(session.get("acc_active"))
        msg = "Request denied. You've deactivated your account. You have to reactivate it before making this request"
        return user_json.request_denied_json_response(msg)

    order_status = db.orders.find_one({"_id": ObjectId(args["order_id"])}, {"order_status": 1, "_id": 0})

    if order_status:
        succeeded = True
        msg = "Request successful"

    else:
        succeeded = True
        msg = "Request unsuccessful. Try again later"

    return user_json.make_get_order_status_response(succeeded, msg, order_status)


@app.route("/match/", methods=['POST'])
@use_args(MatchOrderSchema(), unknown=None)
def match(args):
    if not session.get("user_id"):
        msg = "Request denied. This device is not logged into the server yet"
        return user_json.request_denied_json_response(msg)

    if not session.get("acc_active"):
        print(session.get("acc_active"))
        msg = "Request denied. You've deactivated your account. You have to reactivate it before making this request"
        return user_json.request_denied_json_response(msg)

    # Check if the order exists
    order = db.orders.find_one({"_id": (ObjectId(args["order_id"]))})
    if not order:
        msg = "The order with id, " + args["order_id"] + ", doesn't exist"
        return user_json.match_response_json(False, msg, None)

    # Prevent self-matching
    if order["customer"]["user_id"] == args["user"]["user_id"]:
        msg = "You created this order. You can't self-match"
        return user_json.match_response_json(False, msg, None)

    # Ensure the order hasn't been cancelled
    if order["order_status"] == "cancelled":
        msg = "The order with id, " + args["order_id"] + ", has been cancelled by the customer"
        return user_json.match_response_json(False, msg, None)

    result = db.orders.update_one(user_json.match_order_filter_json(ObjectId(args["order_id"])),
                                  {"$set": user_json.match_unmatch_customer_json(args["user"])}, )

    if result.modified_count:
        msg = "Request completed. You've been matched with the order"

    else:
        msg = "Request not completed. The order has already been matched"

    # Returns the current user info of the customer in case they updated their info before the match
    return user_json.match_response_json(bool(result.modified_count), msg, order["customer"])


@app.route("/unmatch/", methods=['POST'])
@use_args(UserIdOrderIdSchema(), unknown=None)
def unmatch(args):
    if not session.get("user_id"):
        msg = "Request denied. This device is not logged into the server yet"
        return user_json.request_denied_json_response(msg)

    if not session.get("acc_active"):
        print(session.get("acc_active"))
        msg = "Request denied. You've deactivated your account. You have to reactivate it before making this request"
        return user_json.request_denied_json_response(msg)

    # Check if the order exists
    order = db.orders.find_one({"_id": (ObjectId(args["order_id"]))})
    if not order:
        msg = "The order with id, " + args["order_id"] + ", doesn't exist"
        return user_json.success_response_json(False, msg)

    # if order["customer"]["user_id"] == args["user_id"] and (args["order_status"] != "matched" or )

    result = db.orders.update_one(
        user_json.unmatch_order_filter_json(ObjectId(args["order_id"]), args["user_id"]),
        {"$set": user_json.match_unmatch_customer_json(order_status="pending")}, )

    if result.modified_count:
        msg = "Request completed. Order with id, " + args["order_id"] + " is back to pending status"

    else:
        msg = "The request was unsuccessful. The order did not have a deliverer to unmatch"

    return user_json.success_response_json(bool(result.modified_count), msg)


@app.route("/cancel_order/", methods=['POST'])
@use_args(UserIdOrderIdSchema(), unknown=None)
def cancel_order(args):
    if not session.get("user_id"):
        msg = "Request denied. This device is not logged into the server yet"
        return user_json.request_denied_json_response(msg)

    if not session.get("acc_active"):
        print(session.get("acc_active"))
        msg = "Request denied. You've deactivated your account. You have to reactivate it before making this request"
        return user_json.request_denied_json_response(msg)

    # Check if the order exists
    order = db.orders.find_one({"_id": (ObjectId(args["order_id"]))})
    if not order:
        msg = "The order with id, " + args["order_id"] + ", doesn't exist"
        return user_json.success_response_json(False, msg)

    result = db.orders.update_one(
        user_json.cancel_order_filter_json(ObjectId(args["order_id"]), args["user_id"]),
        {"$set": user_json.match_unmatch_customer_json(order_status="cancelled")}, )

    if not result.matched_count:  # Ensure the user has permission to cancel the order
        msg = "You don't have permission to cancel this order"

    elif result.modified_count:  # Check for order cancellation
        msg = "Request completed. Order with id, " + args["order_id"] + " cancelled"

    else:
        msg = "The request was unsuccessful. The order has already been cancelled"

    return user_json.success_response_json(bool(result.modified_count), msg)


@app.route("/orders/", methods=['POST'])
@use_args(UserIdSchema(), unknown=None)
def show_orders(args):
    if not session.get("user_id"):
        msg = "Request denied. This device is not logged into the server yet"
        return user_json.request_denied_json_response(msg)

    cursor = db.orders.find(user_json.show_orders_input_json(args["user_id"]))

    return json_util.dumps(user_json.show_orders_response_json(cursor))


@app.route("/deliveries/", methods=['POST'])
@use_args(UserIdSchema(), unknown=None)
def show_deliveries(args):
    if not session.get("user_id"):
        msg = "Request denied. This device is not logged into the server yet"
        return user_json.request_denied_json_response(msg)

    cursor = db.orders.find(user_json.show_deliveries_input_json(args["user_id"]))

    return json_util.dumps(user_json.show_deliveries_response_json(cursor))


# Return data validation errors as a JSON object
@app.errorhandler(422)
@app.errorhandler(400)
def handle_error(err):
    headers = err.data.get("headers", None)
    messages = err.data.get("messages", ["Invalid request."]).get("json")
    if headers:
        return user_json.validation_errors_json(messages), err.code, headers
    else:
        return user_json.validation_errors_json(messages), err.code


docs.register(create_account)
docs.register(show_users)
docs.register(show_orders)
