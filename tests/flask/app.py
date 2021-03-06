import redis
import stripe
from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from bson import json_util
from cas import CASClient
from werkzeug.utils import redirect
import tests.flask.database_and_response_jsons as json
from random_username.generate import generate_username

from bson.objectid import ObjectId
from datetime import timedelta
from flask import Flask, request, session, url_for, jsonify
from flask_socketio import SocketIO, join_room, send, emit
from flask_session import Session
from logic.customer_finder import CustomerFinder
from tests.flask.helper_functions import validate_password
from tests.flask.mongo_client_connection import MongoClientConnection
from tests.flask.utils.Constants import ORDER_STATUS_UPDATE_VALUES
from tests.flask.utils.common_functions import user_is_logged_in, acc_is_active
from tests.flask.utils.payment import compute_token_fee, compute_new_fee, compute_amount
from tests.flask.validate_email import validate_email
from flask_apispec import FlaskApiSpec, doc, marshal_with, use_kwargs
from tests.flask.schemas import *
from tests.flask.expo_notifications import send_push_message

db = MongoClientConnection.get_database()
app = Flask(__name__)
g_count = 0

# Secret key for cryptographically signing session cookies (Value is in bytes)
app.secret_key = getenv("SECRET_KEY")
STRIPE_WEBHOOK_SIG = getenv("STRIPE_WEBHOOK_SIG")
NON_IDEMPOTENT_MODE = getenv("NON_IDEMPOTENT_MODE")
FETCH_EXISTING = not (NON_IDEMPOTENT_MODE and NON_IDEMPOTENT_MODE.lower() == "on")

"Load configuration"
SESSION_TYPE = "redis"
SESSION_REDIS = redis.from_url("redis://:p202d128f66a40a4c6898c7dd732e48b222138fa5d8d1061d0de35ae3e1919765@ec2-"
                               "107-21-59-180.compute-1.amazonaws.com:24529")

app.config.from_object(__name__)
# Session(app)

# Set up documentation for endpoints
SERVER_TYPE = getenv("SERVER_TYPE")
app.config.update({
    'APISPEC_SPEC': APISpec(
        title=f"DEATS {SERVER_TYPE} Server API Reference",
        version="2.0.0",
        plugins=[MarshmallowPlugin()],
        openapi_version="2.0.0"
    ),
    'APISPEC_SWAGGER_URL': '/DEATS-server-api-json/',
    'APISPEC_SWAGGER_UI_URL': '/DEATS-server-api-ui/'
})

# Socket event naming follows the paradigm --> initiator(cus or del):action:intended_audience(cus or del)
# cus = customer, del = deliverer
socketio = SocketIO(app, manage_session=True, logger=True, engineio_logger=True)

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
@use_kwargs(CreateAccSchema())
@marshal_with(CreateAccResponseSchema, code=200, description="Response json")
@doc(description="Endpoint for creating an account for a new user", tags=['Account: All Roles'])
def create_account(**kwargs):
    try:
        valid_email = validate_email(kwargs["user_info"]["email"])
        user = db.users.find_one({"user_info.email": valid_email.email})
        print("user:", user)
        if user:
            msg = "The Dartmouth email provided is taken. Log in instead if it's your account or use a " \
                  "different valid Dartmouth email address"
            return json.create_acc_response_json(False, msg)

        elif kwargs["password"]:
            # strong password creation is a pain, so allow developers to test without password validation
            if not kwargs["test"]:
                validate_password(kwargs["password"])

            kwargs["user_info"]["email"] = valid_email.email

            # generate a random username for the user that's not already in the db
            username = generate_username()[0]
            print(username)
            while db.users.find_one({"user_info.username": username}):
                username = generate_username()[0]

            kwargs["user_info"]["username"] = username

            result = db.users.insert_one(
                json.create_user_json(kwargs["user_info"], kwargs["password"]))
            msg = "User deets are now on the server"

            user_id = str(result.inserted_id)
            acc_active = True

            # save user session
            session["user_id"] = user_id

            # save account active status for easy access later on
            session["acc_active"] = acc_active

            return json.create_acc_response_json(True, msg, user_id, username, acc_active)

    except ValueError as err:
        return json.create_acc_response_json(False, str(err))


@app.route("/update_acc/", methods=['POST'])
@use_kwargs(UpdateAccSchema())
@marshal_with(SuccessResponseSchema, code=200, description="Response json")
@doc(description="Endpoint for updating an existing account", tags=['Account: All Roles'])
def update_account(**kwargs):
    login_failed = user_is_logged_in()
    if login_failed:
        return login_failed

    # Ensure that if the user provided a new username, it is not already taken
    username = kwargs.get("user_info").get("username")
    if username:
        user = db.users.find_one({"user_info.username": username})
        if user and str(user["_id"]) != session["user_id"]:
            msg = "The request was aborted. You provided a username that already exists on the server"
            return json.success_response_json(False, msg)

    succeeded = 0
    if kwargs.get("password"):
        if not kwargs["test"]:
            try:
                validate_password(kwargs["password"])

            except ValueError as err:
                return json.success_response_json(False, str(err))

        result = db.users.update_one({"_id": ObjectId(session["user_id"])},
                                     {"$set": {"password": kwargs["password"]}})

        succeeded = max(succeeded, result.modified_count)

    if kwargs.get("user_info"):
        for key, value in kwargs["user_info"].items():
            result = db.users.update_one({"_id": ObjectId(session["user_id"])},
                                         {"$set": {f"user_info.{key}": value}})

            succeeded = max(succeeded, result.modified_count)

    # bulk update message; might do individual messaging in the future
    msg = "The user's account has been updated" if succeeded else "The request was not completed. Nothing new was" \
                                                                  " passed"
    return json.success_response_json(bool(succeeded), msg)


@app.route("/delete_acc/", methods=['POST'])
@use_kwargs(UserIdSchema())
@marshal_with(SuccessResponseSchema, code=200, description="Response json")
@doc(description="Endpoint for deleting an existing account", tags=['Account: All Roles'])
def delete_account(**kwargs):
    login_failed = user_is_logged_in()
    if login_failed:
        return login_failed

    result = db.users.delete_one({"_id": ObjectId(session["user_id"])})
    if result.deleted_count:
        msg = "User with id, " + session["user_id"] + ", has been deleted from the server"
        session.pop("user_id", default=None)

    else:
        msg = "Request unsuccessful. No user with id, " + session["user_id"] + ", exists on the server"
    return json.success_response_json(bool(result.deleted_count), msg)


@app.route("/deactivate_acc/", methods=['POST'])
@use_kwargs(UserIdSchema())
@marshal_with(SuccessResponseSchema, code=200, description="Response json")
@doc(description="Endpoint for deactivating an existing account", tags=['Account: All Roles'])
def deactivate_account(**kwargs):
    login_failed = user_is_logged_in()
    if login_failed:
        return login_failed

    result = db.users.update_one({"_id": ObjectId(session["user_id"])},
                                 {"$set": {"acc_active": False}}, )

    print("deactivate_acc result:", result.raw_result)
    if not result.matched_count:
        msg = "The account with id, " + session["user_id"] + ", does not exist on the server"

    elif result.modified_count:
        msg = "User with id, " + session["user_id"] + ", has been deactivated on the server"
        session["acc_active"] = False

    else:
        msg = "The account for user with id, " + session["user_id"] + ", is already deactivated"

    return json.success_response_json(bool(result.modified_count), msg)


@app.route("/reactivate_acc/", methods=['POST'])
@use_kwargs(UserIdSchema())
@marshal_with(SuccessResponseSchema, code=200, description="Response json")
@doc(description="Endpoint for reactivating an existing account in a deactivated state", tags=['Account: All Roles'])
def reactivate_account(**kwargs):
    login_failed = user_is_logged_in()
    if login_failed:
        return login_failed

    result = db.users.update_one({"_id": ObjectId(session["user_id"])},
                                 {"$set": {"acc_active": True}}, )
    print("reactivate_acc result:", result.raw_result)
    if not result.matched_count:
        msg = "The account with id, " + session["user_id"] + ", does not exist on the server"

    elif result.modified_count:
        msg = "User with id, " + session["user_id"] + ", has been reactivated on the server"
        session["acc_active"] = True

    else:
        msg = "The account for user with id, " + session["user_id"] + ", is already active"

    return json.success_response_json(bool(result.modified_count), msg)


@app.route("/sso_login/")
@marshal_with(SSOLoginResponseSchema, code=200, description="Response json")
@doc(description="Endpoint for creating a new account for or logging a user in through Dartmouth SSO",
     tags=['Account: All Roles'])
def sso_login():
    expo_push_token = request.args.get('expoPushToken')
    print("expo_push_token:", expo_push_token)
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
        result_find = None

        if FETCH_EXISTING:
            result_find = db.users.find_one({"user_info.email": net_id_email})

        if result_find:
            print("This user is already in the system. Fetching details...")
            msg = "You've logged into DEATS successfully through Dartmouth SSO"
            print(result_find)
            user_id = str(result_find["_id"])
            acc_active = result_find["acc_active"]
            name = result_find["user_info"]["name"]
            username = result_find["user_info"]["username"]
            phone_num = result_find["user_info"]["phone_num"]

            # save account active status for easy access later on
            session["acc_active"] = result_find.get("acc_active")

        else:
            print("This user is not in the system. Creating a new account for them...")
            name = attributes.get("name")

            # generate a random username for the user that's not already in the db
            username = generate_username()[0]
            print(username)
            while db.users.find_one({"user_info.username": username}):
                username = generate_username()[0]

            user_info = json.create_user_info_json(net_id_email, username, name)

            result_insert = db.users.insert_one(json.create_user_json(user_info, expo_push_token))
            msg = "You've successfully created an account with DEATS through Dartmouth SSO"
            user_id = str(result_insert.inserted_id)
            acc_active = True
            phone_num = None

            # save account active status for easy access later on
            session["acc_active"] = acc_active

        # save user session
        session["user_id"] = user_id

        if expo_push_token and expo_push_token != "undefined":
            send_push_message(expo_push_token, "New DEATS message",
                              "You've successfully logged in through Dartmouth SSO")

        return json.sso_login_response_json(True,
                                            msg,
                                            user_id,
                                            acc_active,
                                            name,
                                            username,
                                            net_id_email,
                                            phone_num,
                                            attributes.get("isFromNewLogin"),
                                            attributes.get("authenticationDate")
                                            )


@app.route("/sso_logout/")
@marshal_with(SuccessResponseSchema, code=200, description="Response json")
@doc(description="Endpoint for logging out a user logged in through Dartmouth SSO", tags=['Account: All Roles'])
def sso_logout():
    # login_failed = user_is_logged_in()
    # if login_failed:
    #     return login_failed

    logout_url = cas_client.get_logout_url()
    print("logout_url", logout_url)
    session.pop("user_id", default=None)
    session.pop("acc_active", default=None)

    return redirect(logout_url)


@app.route("/login/", methods=['POST'])
@use_kwargs(LoginSchema())
@marshal_with(LoginResponseSchema, code=200, description="Response json")
@doc(description="Endpoint for logging a user into an existing non-SSO account", tags=['Account: All Roles'])
def login(**kwargs):
    succeeded = False
    user_id = None
    user_info = None
    acc_active = None

    try:
        valid_email = validate_email(kwargs["user_info"]["email"])
        user = db.users.find_one({"user_info.email": valid_email.email})
        print("email_check", user)
        if not user:
            msg = "The Dartmouth email provided does not exist on the server"

        elif user["password"] != kwargs["password"]:
            msg = "The provided Dartmouth email exists but the password doesn't match what's on the server"

        else:
            succeeded = True
            msg = "Yayy, the user exists!"
            user_id = str(user["_id"])
            user_info = user["user_info"]
            acc_active = user["acc_active"]

            # save user session
            session["user_id"] = user_id

            # save account active status for easy access later on
            session["acc_active"] = user.get("acc_active")

        return json.login_response_json(succeeded, msg, user_id, user_info, acc_active)

    except ValueError as err:
        return json.success_response_json(False, str(err))


@app.route("/logout/", methods=['POST'])
@use_kwargs(UserIdSchema())
@marshal_with(SuccessResponseSchema, code=200, description="Response json")
@doc(description="Endpoint for logging a user out of a non-SSO account", tags=['Account: All Roles'])
def logout(**kwargs):
    login_failed = user_is_logged_in()
    if login_failed:
        return login_failed

    user_id = session.pop("user_id", default=None)
    if user_id:
        succeeded = True
        msg = "The user with id, " + user_id + ", has been logged out"
    else:
        succeeded = False
        msg = "The request was unsuccessful. The user has already been logged out"

    return json.success_response_json(succeeded, msg)


@app.route("/show_users/", methods=['GET'])
def show_users():
    data = request.get_json()
    print("data", data)
    cursor = db.users.find({})
    return json.show_users_response_json(str(list(cursor)))


@app.route("/global_count/", methods=['GET'])
def global_count():
    global g_count
    g_count += 1
    return json.global_count_response_json(g_count)


@app.route("/order_fee/", methods=['POST'])
@use_kwargs(OrderFeeSchema())
@marshal_with(OrderFeeResponseSchema, code=200, description="Response json")
@doc(description="Endpoint for asking for the fee for a given order. Doesn't require a login",
     tags=["Orders: All Roles"])
def compute_order_fee(**kwargs):
    num_unmatched_orders = len(list(db.orders.find(json.find_order_json())))  # find all unmatched orders
    print("number of unmatched orders", num_unmatched_orders)

    order_fee = compute_token_fee(kwargs["pickup_loc"], kwargs["drop_loc"], num_unmatched_orders)
    print("order fee:", order_fee)

    msg = "Here's the cost for this order"
    return json.order_fee_response_json(True, msg, order_fee)


@app.route("/new_order_fee/", methods=['POST'])
@use_kwargs(NewOrderFeeSchema())
@marshal_with(NewOrderFeeResponseSchema, code=200, description="Response json")
@doc(description="Endpoint for asking for the new fee for an updated order. Doesn't require a login",
     tags=["Orders: All Roles"])
def compute_new_order_fee(**kwargs):
    new_order_fee = compute_new_fee(kwargs["new_pickup_loc"], kwargs["new_drop_loc"],
                                    kwargs["old_pickup_loc"], kwargs["old_drop_loc"], kwargs["old_order_fee"])

    msg = "Here's the new cost for this order"
    return json.order_fee_response_json(True, msg, new_order_fee, "new_order_fee")


@app.route("/order_del/", methods=['POST'])
@use_kwargs(OrderDelSchema())
@marshal_with(OrderDelResponseSchema, code=200, description="Response json")
@doc(description="Endpoint for ordering a delivery", tags=["Orders: Customer Role Only"])
def order_delivery(**kwargs):
    login_failed = user_is_logged_in()
    if login_failed:
        return login_failed

    status_check_failed = acc_is_active()
    if status_check_failed:
        return status_check_failed

    # Get the customer info from the db
    customer = db.users.find_one({"_id": ObjectId(session["user_id"])}, {"user_info": 1, "DEATS_tokens": 1, "_id": 0})

    print(customer)

    pickup_loc = kwargs["order"]["pickup_loc"]
    drop_loc = kwargs["order"]["drop_loc"]

    # make sure they have enough DEATS tokens to make the order
    num_unmatched_orders = len(list(db.orders.find(json.find_order_json())))  # find all unmatched orders
    print("number of unmatched orders", num_unmatched_orders)
    order_fee = compute_token_fee(pickup_loc, drop_loc, num_unmatched_orders)
    print("order fee:", order_fee)

    curr_tokens = customer.pop("DEATS_tokens")
    remaining_tokens = curr_tokens - order_fee

    if remaining_tokens < 0:
        msg = "You don't have enough DEATS tokens to make this request"
        return json.order_delivery_response_json(False, msg, curr_tokens, order_fee)

    # If the customer passed in new user info to be used at the time of creating the order, use that instead
    if kwargs.get("user_info"):
        for key, value in kwargs["user_info"].items():
            customer["user_info"][f"{key}"] = value

    customer["user_id"] = session["user_id"]

    order_id = db.orders.insert_one(
        json.order_delivery_json(customer,
                                 pickup_loc, drop_loc,
                                 kwargs["order"]["GET_code"], order_fee)).inserted_id

    if order_id:
        socketio.emit("cus:new:all", str(order_id))  # announce to all connected clients that a new order's been created
        msg = "The order request has been created successfully"

        # charge the user if the order request is successful
        result = db.users.update_one({"_id": ObjectId(session["user_id"])},
                                     {"$set": {"DEATS_tokens": remaining_tokens}})

        if not result.modified_count:
            msg = "Something went wrong. Try again later"
            return json.success_response_json(False, msg)

    else:
        msg = "The request data looks good but the order wasn't created. Try again"
        remaining_tokens = curr_tokens

    order_id = str(order_id)

    return json.order_delivery_response_json(bool(order_id), msg, remaining_tokens, order_fee, order_id)


@app.route("/order_del_with_card/", methods=['POST'])
@use_kwargs(OrderDelSchema())
@doc(description="Endpoint for ordering a delivery with card payment", tags=["Orders: Customer Role Only"])
def order_delivery_with_card(**kwargs):
    login_failed = user_is_logged_in()
    if login_failed:
        return login_failed

    status_check_failed = acc_is_active()
    if status_check_failed:
        return status_check_failed

    num_unmatched_orders = len(list(db.orders.find(json.find_order_json())))  # find all unmatched orders
    print("number of unmatched orders", num_unmatched_orders)

    order = kwargs["order"]
    order_fee = compute_token_fee(order["pickup_loc"], order["drop_loc"], num_unmatched_orders)
    print("order fee:", order_fee)

    return create_payment_sheet_details(
        order_fee, json.create_payment_details_order_json(order, kwargs.get("user_info")))


@app.route("/update_order/", methods=['POST'])
@use_kwargs(UpdateOrderSchema())
@marshal_with(OrderUpdateResponseSchema, code=200, description="Response json")
@doc(description="Endpoint for updating an existing order. To be called only by customers",
     tags=['Orders: Customer Role Only'])
def update_order(**kwargs):
    order_id = kwargs["order"]["order_id"]
    new_order_fee, order = update_order_helper(kwargs)

    old_order_fee = order["order_fee"]

    customer = db.users.find_one({"_id": ObjectId(session["user_id"])},
                                 {"user_info": 1, "DEATS_tokens": 1, "_id": 0})
    print(customer)

    curr_tokens = customer.pop("DEATS_tokens")
    remaining_tokens = curr_tokens + old_order_fee - new_order_fee

    if remaining_tokens < 0:
        msg = "You don't have enough DEATS tokens to make this location update"
        return json.order_delivery_loc_update_response_json(False, msg, curr_tokens, new_order_fee, old_order_fee)

    succeeded = 0
    charge_new_fee = False
    updated_payload = {}  # payload to push to the room for the order
    for key, value in kwargs["order"].items():
        if key != "order_id":
            print("key: ", key, " value: ", value)
            result = db.orders.update_one({"_id": ObjectId(order_id)}, {"$set": {key: value}})

            if result.modified_count:
                succeeded = 1
                updated_payload[key] = value

                # Check for whether a new delivery fee should be charged
                # requires just one or both to be updated
                if key == "pickup_loc" or key == "drop_loc":
                    charge_new_fee = True

    if succeeded:
        msg = "The user's order has been updated"

        if charge_new_fee:
            db.orders.update_one({"_id": ObjectId(order_id)}, {"$set": {"order_fee": new_order_fee}})

        else:
            # if the order is not charged, the remaining tokens is the same as the curr tokens the user have
            remaining_tokens = curr_tokens

        # tell the deliverer the updates if there is one
        if order["deliverer"]:
            socketio.emit("cus:update:del", updated_payload, to=order_id, include_self=False)

        else:
            # announce to all connected clients that an existing order has been updated
            # clients are expected to call make_del to get the fresh update upon receiving this event
            # skip if the only key updated is the GET_code
            # GET_code is only relevant at the time of delivery
            if len(updated_payload) > 1 or "GET_code" not in updated_payload:
                socketio.emit("cus:update:all", order_id)

    else:
        msg = "The request wasn't successful. No new info was provided"

    return json.order_delivery_loc_update_response_json(bool(succeeded), msg,
                                                        remaining_tokens, new_order_fee, old_order_fee)


@app.route("/update_order_with_card/", methods=['POST'])
@use_kwargs(UpdateOrderSchema())
@doc(description="Endpoint for updating an order with card payment", tags=["Orders: Customer Role Only"])
def update_order_with_card(**kwargs):
    new_order_fee, existing_order = update_order_helper(kwargs)

    extra_fee = new_order_fee - existing_order["order_fee"]
    if extra_fee > 0:
        return create_payment_sheet_details(
            extra_fee, json.create_payment_details_order_json(kwargs["order"], kwargs.get("user_info")))


def update_order_helper(kwargs):
    login_failed = user_is_logged_in()
    if login_failed:
        return login_failed

    status_check_failed = acc_is_active()
    if status_check_failed:
        return status_check_failed

    order_id = kwargs["order"]["order_id"]

    # Ensure the order exists
    order = db.orders.find_one({"_id": ObjectId(order_id)})
    if not order:
        msg = "The order with id, " + order_id + ", doesn't exist"
        return json.success_response_json(False, msg)

    # Ensure the order is not canceled
    if order["order_status"] == "canceled":
        msg = "The request was unsuccessful. The order was canceled"
        return json.success_response_json(False, msg)

    # Ensure the user making the update is the customer
    if order["customer"]["user_id"] != session["user_id"]:
        msg = "The request was unsuccessful. You're not the deliverer for this order"
        return json.success_response_json(False, msg)

    # Make sure the customer has enough DEATS tokens to do a location update
    old_pickup_loc = order["pickup_loc"]
    old_drop_loc = order["drop_loc"]

    # Use the provided pickup or (drop location) if there is one
    # Doesn't matter if the location update will succeed or not
    # i.e. if it will succeed, then it is exactly what we want to use in the new fee computation
    # If not, then that means it is the same as what is already on the order, and we can just use that
    new_pickup_loc = kwargs["order"]["pickup_loc"] if kwargs.get("order").get("pickup_loc") else old_pickup_loc
    new_drop_loc = kwargs["order"]["drop_loc"] if kwargs.get("order").get("drop_loc") else old_drop_loc

    new_order_fee = compute_new_fee(new_pickup_loc, new_drop_loc,
                                    old_pickup_loc, old_drop_loc, order["order_fee"])
    print("new order fee:", new_order_fee)
    return new_order_fee, order


@app.route("/update_order_status/", methods=['POST'])
@use_kwargs(UpdateOrderStatusSchema())
@marshal_with(UpdateOrderStatusResponseSchema, code=200, description="Response json")
@doc(description="Endpoint for updating the order status of an existing order. To be called only by deliverers",
     tags=['Orders: Deliverer Role Only'])
def update_order_status(**kwargs):
    login_failed = user_is_logged_in()
    if login_failed:
        return login_failed

    status_check_failed = acc_is_active()
    if status_check_failed:
        return status_check_failed

    # Ensure the status update value is permitted
    order_status = kwargs["order"]["order_status"]
    print(order_status)
    if order_status not in ORDER_STATUS_UPDATE_VALUES and "heading to" not in order_status:
        msg = "The request was aborted. The order status value provided is not permitted"
        return json.success_response_json(False, msg)

    # Ensure the order exists
    order_id = kwargs["order"]["order_id"]
    order = db.orders.find_one({"_id": (ObjectId(order_id))})
    if not order:
        msg = "The order with id, " + order_id + ", doesn't exist"
        return json.success_response_json(False, msg)

    # Ensure the order is not canceled
    if order["order_status"] == "canceled":
        msg = "The request was unsuccessful. The order was canceled"
        return json.success_response_json(False, msg)

    # Ensure the user making the update is the deliverer
    deliverer = order.get("deliverer")
    if not deliverer or (deliverer and deliverer["user_id"] != session["user_id"]):
        msg = "The request was unsuccessful. You're not the deliverer for this order"
        return json.success_response_json(False, msg)

    succeeded = db.orders.update_one({"_id": ObjectId(order_id)},
                                     {"$set": {"order_status": order_status}}).modified_count

    result = None
    if succeeded:
        msg = "The user's order status has been updated"
        socketio.emit("del:order_status:cus", order_status, to=order_id, include_self=False)

        # Pay the deliverer after they've delivered the order
        if order_status == "delivered":
            result = db.users.update_one({"_id": ObjectId(session["user_id"])},
                                         {"$inc": {"DEATS_tokens": order["order_fee"]}})
            if not result.modified_count:
                msg = "The order status was updated but something went wrong with paying the deliverer"
                return json.update_order_status_response_json(True, msg)

            result = db.users.find_one({"_id": ObjectId(session["user_id"])},
                                       {"DEATS_tokens": 1, "_id": 0})["DEATS_tokens"]

    else:
        msg = "The request wasn't successful. No new info was provided"

    return json.update_order_status_response_json(bool(succeeded), msg, result)


@app.route("/make_del/", methods=['POST'])
@use_kwargs(MakeDelSchema())
@marshal_with(StartDelResponseSchema, code=200, description="Response json")
@doc(description="Endpoint for requesting to make a delivery", tags=['Orders: Deliverer Role Only'])
def make_delivery(delivery, **kwargs):
    login_failed = user_is_logged_in()
    if login_failed:
        return login_failed

    status_check_failed = acc_is_active()
    if status_check_failed:
        return status_check_failed

    result = db.users.update_one({"_id": ObjectId(session["user_id"])},
                                 {"$set": json.make_delivery_json(
                                     delivery["leaving_from"], delivery["destination"])}, )
    print("modified: ", result.modified_count, " number of users")

    customer_finder = CustomerFinder(session["user_id"], delivery["destination"],
                                     db.orders.find(json.find_order_json()))

    customer_finder.sort_customers()

    return json.start_delivery_response_json(
        customer_finder.get_k_least_score_customers(delivery["num_deliveries"]))


@app.route("/my_deliverer/", methods=['POST'])
@use_kwargs(OrderIdSchema())
@marshal_with(GetDelivererResponseSchema, code=200, description="Response json")
@doc(description="Endpoint for getting the current deliverer for an existing order",
     tags=['Orders: Customer Role Only'])
def get_my_deliverer(**kwargs):
    login_failed = user_is_logged_in()
    if login_failed:
        return login_failed
    status_check_failed = acc_is_active()

    if status_check_failed:
        return status_check_failed

    # Ensure the order exists
    order = db.orders.find_one({"_id": (ObjectId(kwargs["order_id"]))})
    if not order:
        msg = "The order with id, " + kwargs["order_id"] + ", doesn't exist"
        return json.success_response_json(False, msg)

    # Ensure the user created the order
    if order["customer"]["user_id"] != session["user_id"]:
        msg = "Request denied. You're not the creator of this order"
        return json.success_response_json(False, msg)

    deliverer = order["deliverer"]

    print("deliverer_info:", deliverer)

    msg = "Deliverer found!" if deliverer else "No deliverer for this order yet. Check again later"
    return json.get_my_deliverer_response(True, msg, deliverer)


@app.route("/order_status/", methods=['POST'])
@use_kwargs(UserIdOrderIdSchema())
@marshal_with(GetOrderStatusResponseSchema, code=200, description="Response json")
@doc(description="Endpoint for getting the order status of an existing order."
                 " To be called only by the creator of the order", tags=['Orders: Customer Role Only'])
def get_order_status(**kwargs):
    login_failed = user_is_logged_in()
    if login_failed:
        return login_failed

    status_check_failed = acc_is_active()
    if status_check_failed:
        return status_check_failed

    # Ensure the order exists
    order = db.orders.find_one({"_id": (ObjectId(kwargs["order_id"]))})
    if not order:
        msg = "The order with id, " + kwargs["order_id"] + ", doesn't exist"
        return json.success_response_json(False, msg)

    # Ensure the user created the order
    if order["customer"]["user_id"] != session["user_id"]:
        msg = "Request denied. You're not the creator of this order"
        return json.success_response_json(False, msg)

    msg = "Request successful"
    return json.make_get_order_status_response(True, msg, order["order_status"])


@app.route("/get_code/", methods=['POST'])
@use_kwargs(UserIdOrderIdSchema())
@marshal_with(GETCodeResponseSchema, code=200, description="Response json")
@doc(description="Endpoint for getting the GET code of an existing order", tags=['Orders: All Roles'])
def retrieve_get_code(**kwargs):
    login_failed = user_is_logged_in()
    if login_failed:
        return login_failed

    status_check_failed = acc_is_active()
    if status_check_failed:
        return status_check_failed

    # Ensure the order exists
    order = db.orders.find_one({"_id": (ObjectId(kwargs["order_id"]))})
    if not order:
        msg = "The order with id, " + kwargs["order_id"] + ", doesn't exist"
        return json.success_response_json(False, msg)

    msg = "Request successful"
    return json.make_get_order_status_response(True, msg, order["GET_code"])


@app.route("/match/", methods=['POST'])
@use_kwargs(MatchOrderSchema())
@marshal_with(MatchResponseSchema, code=200, description="Response json")
@doc(description="Endpoint for matching a deliverer with an existing order", tags=['Orders: Deliverer Role Only'])
def match(**kwargs):
    login_failed = user_is_logged_in()
    if login_failed:
        return login_failed

    status_check_failed = acc_is_active()
    if status_check_failed:
        return status_check_failed

    # Ensure the order exists
    order = db.orders.find_one({"_id": (ObjectId(kwargs["order_id"]))})
    if not order:
        msg = "The order with id, " + kwargs["order_id"] + ", doesn't exist"
        return json.match_response_json(False, msg, None)

    # Prevent self-matching
    if order["customer"]["user_id"] == session["user_id"]:
        msg = "You created this order. You can't self-match"
        return json.match_response_json(False, msg, None)

    # Ensure the order hasn't been canceled
    if order["order_status"] == "canceled":
        msg = "You can't match with this order. It has been canceled by the customer"
        return json.match_response_json(False, msg, None)

    # Get the deliverer info from the db
    deliverer = db.users.find_one({"_id": ObjectId(session["user_id"])}, {"user_info": 1, "_id": 0})

    # If the deliverer passed in new user info to be used at the time of making the delivery request, use that instead
    if kwargs.get("user_info"):
        for key, value in kwargs["user_info"].items():
            deliverer["user_info"][f"{key}"] = value

    deliverer["user_id"] = session["user_id"]

    result = db.orders.update_one(json.match_order_filter_json(ObjectId(kwargs["order_id"])),
                                  {"$set": json.match_unmatch_customer_json(deliverer)}, )

    customer = order["customer"]
    if result.modified_count:
        msg = "Request completed. You've matched with the customer on the order"

        # announce to all connected clients that the order has been matched and no longer available
        socketio.emit("del:match:all", kwargs["order_id"])

    elif order["deliverer"]["user_id"] == session["user_id"]:
        msg = "You've already matched with the customer on this order"

    else:
        msg = "Request not completed. The customer on the order has already been matched with a different deliverer"
        customer = None

    # Returns the current user info of the customer in case they updated their info before the match
    return json.match_response_json(bool(result.modified_count), msg, customer)


@app.route("/unmatch/", methods=['POST'])
@use_kwargs(UserIdOrderIdSchema())
@marshal_with(SuccessResponseSchema, code=200, description="Response json")
@doc(description="Endpoint for un-matching a deliverer from an existing order. "
                 "To be called by either the creator or deliverer on the order only", tags=['Orders: All Roles'])
def unmatch(**kwargs):
    login_failed = user_is_logged_in()
    if login_failed:
        return login_failed

    status_check_failed = acc_is_active()
    if status_check_failed:
        return status_check_failed

    order_id = kwargs["order_id"]

    # Ensure the order exists
    order = db.orders.find_one({"_id": (ObjectId(order_id))})
    if not order:
        msg = "The order with id, " + order_id + ", doesn't exist"
        return json.success_response_json(False, msg)

    # Ensure the order is not canceled
    if order["order_status"] == "canceled":
        msg = "The request was unsuccessful. The order was canceled"
        return json.success_response_json(False, msg)

    # Ensure the order has a deliverer
    if not order["deliverer"]:
        msg = "The request was unsuccessful. The order did not have a deliverer to unmatch from"
        return json.success_response_json(False, msg)

    # Customers can unmatch a deliverer from an order only if the order is not canceled and not past matched
    if order["customer"]["user_id"] == session["user_id"] and order["order_status"] != "matched":
        msg = "You can't unmatch the deliverer form this order; they're already on their way"
        return json.success_response_json(False, msg)

    result = db.orders.update_one(
        json.unmatch_order_filter_json(ObjectId(order_id), session["user_id"]),
        {"$set": json.match_unmatch_customer_json(order_status="pending")}, )

    if not result.matched_count:
        msg = "You can't unmatch the deliverer from this order. You're not the creator or the deliverer for the order"

    elif result.modified_count:
        socketio.emit("cus:unmatch:del", {"order_id": order_id, "reason": kwargs["reason"]}, to=order_id)

        # announce to all connected clients that an order has been unmatched and is now available
        # clients would have to call make_del to get the fresh update
        socketio.emit("cus:unmatch:all", order_id)

        msg = "Request completed. Order with id, " + order_id + " is back to pending status"

    else:
        msg = "The request was unsuccessful. The order did not have a deliverer to unmatch from"

    return json.success_response_json(bool(result.modified_count), msg)


@app.route("/cancel_order/", methods=['POST'])
@use_kwargs(UserIdOrderIdSchema())
@marshal_with(SuccessResponseSchema, code=200, description="Response json")
@doc(description="Endpoint for canceling an existing order. Accessible to only the order creator",
     tags=['Orders: Customer Role Only'])
def cancel_order(**kwargs):
    login_failed = user_is_logged_in()
    if login_failed:
        return login_failed
    status_check_failed = acc_is_active()
    if status_check_failed:
        return status_check_failed

    order_id = kwargs["order_id"]

    # Ensure the order exists
    order = db.orders.find_one({"_id": (ObjectId(order_id))})
    if not order:
        msg = "The order with id, " + order_id + ", doesn't exist"
        return json.success_response_json(False, msg)

    # Ensure the user has permission to cancel the order
    if order["customer"]["user_id"] != session["user_id"]:
        msg = "You did not create this order. You don't have permission to cancel it"
        return json.success_response_json(False, msg)

    # Ensure the order is cancelable.
    # Note: orders in progress cannot be canceled
    if order["order_status"] != "pending":
        if order["order_status"] == "canceled":
            msg = "The request was unsuccessful. The order has already been canceled"

        else:
            msg = "This order is no more cancelable. The deliverer is bringing your food"

        return json.success_response_json(False, msg)

    result = db.orders.update_one(
        json.cancel_order_filter_json(ObjectId(order_id), session["user_id"]),
        {"$set": json.match_unmatch_customer_json(order_status="canceled")}, )

    if result.modified_count:  # Check for order cancellation
        if order["deliverer"]:
            socketio.emit("cus:cancel:del", {"reason": kwargs["reason"]}, to=order_id, include_self=False)

        else:
            # announce to all connected clients that an order has been canceled and is now available
            # clients would have to take the necessary action to remove the order from their list of unmatched orders
            socketio.emit("cus:cancel:all", order_id)

        msg = "Request completed. Order with id, " + order_id + " has been canceled"

    else:
        msg = "Request unsuccessful"

    return json.success_response_json(bool(result.modified_count), msg)


@app.route("/orders/", methods=['POST'])
@use_kwargs(UserIdSchema())
@marshal_with(GetOrdersResponseSchema, code=200, description="Response json")
@doc(description="Endpoint for getting all existing orders", tags=['Orders: All Roles'])
def show_orders(**kwargs):
    login_failed = user_is_logged_in()
    if login_failed:
        return login_failed

    orders = db.orders.find(json.show_orders_input_json(session["user_id"]))

    msg = "Here's a list of orders you've made" if len(list(orders.clone())) else "You've not made any orders yet"
    return json.show_orders_response_json(True, msg, orders)


@app.route("/deliveries/", methods=['POST'])
@use_kwargs(UserIdSchema())
@marshal_with(GetDeliveriesResponseSchema, code=200, description="Response json")
@doc(description="Endpoint for getting all existing deliveries", tags=['Orders: All Roles'])
def show_deliveries(**kwargs):
    login_failed = user_is_logged_in()
    if login_failed:
        return login_failed

    orders = db.orders.find(json.show_deliveries_input_json(session["user_id"]))

    msg = "Here's a list of deliveries you've made" if len(list(orders.clone())) \
        else "You've not made any deliveries yet"
    return json.show_deliveries_response_json(True, msg, orders)


@app.route("/all_orders/", methods=['POST'])
@use_kwargs(UserIdSchema())
@marshal_with(AllOrdersResponseSchema, code=200, description="Response json")
@doc(description="Endpoint for getting all existing orders", tags=['Orders: All Roles'])
def all_orders(**kwargs):
    return fetch_orders(
        json.fetch_orders_input_json(session["user_id"], "customer"),
        "all",
        "orders")


@app.route("/active_orders/", methods=['POST'])
@use_kwargs(UserIdSchema())
@marshal_with(ActiveOrdersResponseSchema, code=200, description="Response json")
@doc(description="Endpoint for getting all active orders", tags=['Orders: All Roles'])
def active_orders(**kwargs):
    return fetch_orders(
        json.fetch_active_orders_input_json(session["user_id"], "customer"),
        "active",
        "orders"
    )


@app.route("/past_orders/", methods=['POST'])
@use_kwargs(UserIdSchema())
@marshal_with(PastOrdersResponseSchema, code=200, description="Response json")
@doc(description="Endpoint for getting all past orders", tags=['Orders: All Roles'])
def past_orders(**kwargs):
    return fetch_orders(
        json.fetch_orders_input_json(session["user_id"], "customer", "delivered"),
        "past",
        "orders")


@app.route("/canceled_orders/", methods=['POST'])
@use_kwargs(UserIdSchema())
@marshal_with(CanceledOrdersResponseSchema, code=200, description="Response json")
@doc(description="Endpoint for getting canceled orders", tags=['Orders: All Roles'])
def canceled_orders(**kwargs):
    return fetch_orders(
        json.fetch_orders_input_json(session["user_id"], "customer", "canceled"),
        "canceled",
        "orders")


@app.route("/all_deliveries/", methods=['POST'])
@use_kwargs(UserIdSchema())
@marshal_with(AllDeliveriesResponseSchema, code=200, description="Response json")
@doc(description="Endpoint for getting all existing deliveries", tags=['Orders: All Roles'])
def all_deliveries(**kwargs):
    return fetch_orders(
        json.fetch_orders_input_json(session["user_id"], "deliverer"),
        "all",
        "deliveries")


@app.route("/active_deliveries/", methods=['POST'])
@use_kwargs(UserIdSchema())
@marshal_with(ActiveDeliveriesResponseSchema, code=200, description="Response json")
@doc(description="Endpoint for getting all active deliveries", tags=['Orders: All Roles'])
def active_deliveries(**kwargs):
    return fetch_orders(
        json.fetch_active_orders_input_json(session["user_id"], "deliverer"),
        "active",
        "deliveries"
    )


@app.route("/past_deliveries/", methods=['POST'])
@use_kwargs(UserIdSchema())
@marshal_with(PastDeliveriesResponseSchema, code=200, description="Response json")
@doc(description="Endpoint for getting all past deliveries", tags=['Orders: All Roles'])
def past_deliveries(**kwargs):
    return fetch_orders(
        json.fetch_orders_input_json(session["user_id"], "deliverer", "delivered"),
        "past",
        "deliveries")


@app.route("/canceled_deliveries/", methods=['POST'])
@use_kwargs(UserIdSchema())
@marshal_with(CanceledDeliveriesResponseSchema, code=200, description="Response json")
@doc(description="Endpoint for getting all canceled deliveries", tags=['Orders: All Roles'])
def canceled_deliveries(**kwargs):
    return fetch_orders(
        json.fetch_orders_input_json(session["user_id"], "deliverer", "canceled"),
        "canceled",
        "deliveries")


def fetch_orders(filter_json, result_modifier, result_type):
    login_failed = user_is_logged_in()
    if login_failed:
        return login_failed

    result = db.orders.find(filter_json)

    msg = f"Here's the list of {result_modifier} {result_type} you've made" if len(list(result.clone())) \
        else f"There are no {result_modifier} {result_type} in your account"

    return json.fetch_orders_response_json(True, msg, result, result_modifier, result_type)


@app.route("/buy_DEATS_tokens/", methods=['POST'])
@use_kwargs(BuyDEATSTokensSchema())
@doc(description="Endpoint for buying DEATS tokens", tags=["Orders: All Roles"])
def buy_DEATS_tokens(**kwargs):
    return create_payment_sheet_details(kwargs["DEATS_tokens"])


def create_payment_sheet_details(tokens, order=None):
    stripe.api_key = getenv("STRIPE_SECRET_KEY")
    # Use an existing Customer ID if this is a returning customer
    customer = stripe.Customer.create()
    ephemeral_key = stripe.EphemeralKey.create(
        customer=customer['id'],
        stripe_version='2020-08-27',
    )

    amount = compute_amount(tokens)
    print("amount", amount)
    payment_intent = stripe.PaymentIntent.create(
        amount=int(amount),
        currency='usd',
        customer=customer['id'],
        automatic_payment_methods={
            'enabled': True  # use the payment methods configured in the DEATS Stripe Dashboard
        }
    )

    print("created payment_intent: ", payment_intent.id, payment_intent)

    result = db.payments.insert_one(
        json.create_payment_json(payment_intent.id, session["user_id"], tokens, order))

    print("payment: ", result.inserted_id)

    return jsonify(paymentIntentId=payment_intent.id,
                   paymentIntentClientSecret=payment_intent.client_secret,
                   ephemeralKey=ephemeral_key.secret,
                   customer=customer.id,
                   publishableKey=getenv("STRIPE_PUBLISHABLE_KEY"))


@app.route("/stripe_webhook_updates", methods=['POST'])
def stripe_webhook_updates():
    data = request.data
    print(data)

    stripe_signature = request.headers["STRIPE_SIGNATURE"]
    print("stripe_signature", stripe_signature)
    print("STRIPE_WEBHOOK_SIG", STRIPE_WEBHOOK_SIG)

    try:
        event = stripe.Webhook.construct_event(
            data, stripe_signature, STRIPE_WEBHOOK_SIG
        )
    except ValueError as err:
        # Invalid event data
        return json.success_response_json(False, str(err))

    except stripe.error.SignatureVerificationError as err:
        # Invalid signature
        return json.success_response_json(False, str(err))

    # Event handlers
    if event['type'] == 'payment_intent.canceled':
        payment_intent = event['data']['object']
        print("Canceled payment intent: ", payment_intent)

    elif event['type'] == 'payment_intent.payment_failed':
        payment_intent = event['data']['object']
        print(payment_intent)

    elif event['type'] == 'payment_intent.processing':
        payment_intent = event['data']['object']
        print("Processing payment intent: ", payment_intent)

    elif event['type'] == 'payment_intent.succeeded':
        payment_intent = event['data']['object']
        print("Succeeded payment intent: ", payment_intent)

        payment = db.payments.find_one({"_id": payment_intent.id})
        pay_tokens = payment["tokens"]  # tokens paid by the customer

        # Get the customer info from the db
        customer = db.users.find_one({"_id": ObjectId(payment["user_id"])}, {"DEATS_tokens": 1, "_id": 0})
        curr_tokens = customer.pop("DEATS_tokens")

        pay_order = payment["pay_order"]
        if pay_order:  # The payment has an order attached to it (implies order creation or update)
            order_id = pay_order["order"].get("order_id")
            print(order_id)

            if order_id:  # The payment has an order id attached to it (implies order update)
                succeeded = 0
                updated_payload = {}  # payload to push to the room for the order

                # Get the existing order before any updates
                existing_order = db.orders.find_one({"_id": ObjectId(order_id)})
                for key, value in pay_order["order"].items():
                    if key != "order_id":
                        print("key: ", key, " value: ", value)
                        result = db.orders.update_one({"_id": ObjectId(order_id)}, {"$set": {key: value}})

                        if result.modified_count:
                            succeeded = 1
                            updated_payload[key] = value

                old_order_fee = existing_order["order_fee"]
                new_order_fee = pay_tokens + old_order_fee
                if succeeded:
                    msg = "The user's order has been updated"

                    db.orders.update_one({"_id": ObjectId(order_id)}, {"$inc": {"order_fee": pay_tokens}})

                    socketio.emit("stripe:update_order_wc:cus",  # update_order_wc = update_order_with_card
                                  json.order_delivery_loc_update_response_json(
                                      bool(succeeded),
                                      msg,
                                      curr_tokens,
                                      new_order_fee,
                                      old_order_fee),
                                  to=payment_intent.id,
                                  include_self=False)  # emit the updated order response to the order creator

                    # tell the deliverer the updates if there is one
                    if existing_order["deliverer"]:
                        socketio.emit("cus:update:del", updated_payload, to=order_id, include_self=False)

                    else:
                        # announce to all connected clients that an existing order has been updated
                        # clients are expected to call make_del to get the fresh update upon receiving this event
                        # skip if the only key updated is the GET_code
                        # GET_code is only relevant at the time of delivery
                        if len(updated_payload) > 1 or "GET_code" not in updated_payload:
                            socketio.emit("cus:update:all", order_id)

                else:
                    msg = "The request wasn't successful. No new info was provided"

                return json.order_delivery_loc_update_response_json(bool(succeeded), msg, curr_tokens,
                                                                    new_order_fee, old_order_fee)

            else:  # No order id attached; implies order creation
                # If the customer passed in new user info to be used at the time of creating the order, use that instead
                if pay_order.get("user_info"):
                    for key, value in pay_order["user_info"].items():
                        customer["user_info"][f"{key}"] = value

                customer["user_id"] = payment["user_id"]

                order_id = db.orders.insert_one(
                    json.order_delivery_json(customer,
                                             pay_order["order"]["pickup_loc"], pay_order["order"]["drop_loc"],
                                             pay_order["order"]["GET_code"], pay_tokens)).inserted_id

                if order_id:
                    msg = "The order request has been created successfully"
                    order_id = str(order_id)
                    socketio.emit("stripe:order_wc:cus",  # order_wc = order_with_card
                                  json.order_delivery_response_json(
                                      bool(order_id),
                                      msg,
                                      curr_tokens,
                                      pay_tokens,
                                      order_id),
                                  to=payment_intent.id,
                                  include_self=False)  # emit the order details to the initiator of this order

                    socketio.emit("cus:new:all",
                                  order_id)  # announce to all connected clients that a new order's been created

                else:
                    msg = "The request data looks good but the order wasn't created. Try again"

                order_id = str(order_id)

                return json.order_delivery_response_json(bool(order_id), msg, None, pay_tokens, order_id)

        else:  # No order attached implies buy DEATS tokens
            succeeded = True
            msg = "Your DEATS_tokens has been updated"
            rem_tokens = curr_tokens + pay_tokens

            result = db.users.update_one({"_id": ObjectId(payment["user_id"])},
                                         {"$inc": {"DEATS_tokens": pay_tokens}})
            if not result.modified_count:
                succeeded = False
                msg = "The request went through but something went wrong with updating the user's DEATS tokens"
                rem_tokens = None

            socketio.emit("stripe:buy_tokens:cus",
                          json.buy_DEATS_tokens_response_json(succeeded, msg, rem_tokens),
                          to=payment_intent.id, include_self=False)  # emit the order details to the initiator of this order

            return json.buy_DEATS_tokens_response_json(succeeded, msg)

    # Other event types
    else:
        print('Unhandled event type {}'.format(event['type']))

    msg = "The webhook update was processed successfully"
    return json.success_response_json(True, msg)


@socketio.on('connect')
def on_connect():
    print("New connection")


@socketio.on('disconnect')
def on_disconnect():
    print("Client disconnected")


@socketio.on("join_order_room")
def join_order_room(data):
    print("on join data: ", data)
    print("session: ", session)

    # user_id = session["user_id"]
    user_id = data["user_id"]
    order_id = data["order_id"]

    # add the user to a room based on the order_id passed
    join_room(order_id)

    order = db.orders.find_one({"_id": (ObjectId(order_id))})
    if order.get("deliverer") and order.get("deliverer")["user_id"] == user_id:
        emit("del:match:cus", {"order_id": order_id, "deliverer": order["deliverer"]}, to=order_id, include_self=False)

    else:
        send("The user " + user_id + " has started a new order room: " + order_id, to=order_id, include_self=False)

    msg = "The user has been successfully added to the order room " + order_id
    return json.success_response_json(True, msg)


@socketio.on("join_payment_room")
def join_payment_room(data):
    print("on join data: ", data)
    print("session: ", session)

    # user_id = session["user_id"]
    user_id = data["user_id"]
    payment_intent_id = data["payment_intent_id"]

    # add the user to a room based on the order_id passed
    join_room(payment_intent_id)
    send("The user " + user_id + " has started a new payment room: " + payment_intent_id,
         to=payment_intent_id, include_self=False)

    msg = "The user has been successfully added to the payment room " + payment_intent_id
    return json.success_response_json(True, msg)


# Return data validation errors as a JSON object
@app.errorhandler(422)
@app.errorhandler(400)
def handle_error(err):
    headers = err.data.get("headers", None)
    messages = err.data.get("messages", ["Invalid request."]).get("json")
    if headers:
        return json.validation_errors_json(messages), err.code, headers
    else:
        return json.validation_errors_json(messages), err.code


# account
docs.register(create_account)
docs.register(update_account)
docs.register(delete_account)
docs.register(deactivate_account)
docs.register(reactivate_account)
docs.register(sso_login)
docs.register(sso_logout)
docs.register(login)
docs.register(logout)

# orders
docs.register(order_delivery)
docs.register(update_order)
docs.register(make_delivery)
docs.register(get_my_deliverer)
docs.register(get_order_status)
docs.register(update_order_status)
docs.register(retrieve_get_code)
docs.register(match)
docs.register(unmatch)
docs.register(cancel_order)
docs.register(show_orders)
docs.register(show_deliveries)
