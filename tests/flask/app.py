import redis
from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from bson import json_util
from cas import CASClient
from werkzeug.utils import redirect
import tests.flask.database_and_response_jsons as json

from bson.objectid import ObjectId
from datetime import timedelta
from flask import Flask, request, session, url_for
from flask_session import Session
from logic.customer_finder import CustomerFinder
from tests.flask.helper_functions import validate_password
from tests.flask.mongo_client_connection import MongoClientConnection
from tests.flask.utils.common_functions import login_check, acc_status_check
from tests.flask.validate_email import validate_email
from flask_apispec import FlaskApiSpec, doc, marshal_with, use_kwargs
from tests.flask.schemas import *

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
        openapi_version="2.0.0"
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
@use_kwargs(CreateAccSchema())
@marshal_with(CreateAccResponseSchema, code=200, description="Response json")
@doc(description="Endpoint for creating an account for a new user", tags=['Account'])
def create_account(**kwargs):
    try:
        valid_email = validate_email(kwargs["user_info"]["email"])
        user = db.users.find_one({"user_info.email": valid_email.email})
        print("user:", user)
        if user:
            msg = "The Dartmouth email provided is taken. Log in instead if it's your account or use a " \
                  "different email address"
            return json.create_acc_response_json(False, msg)

        elif kwargs["password"]:
            # strong password creation is a pain, so allow developers to test without password validation
            if not kwargs["test"]:
                validate_password(kwargs["password"])

            kwargs["user_info"]["email"] = valid_email.email
            result = db.users.insert_one(
                json.create_user_json(kwargs["user_info"], kwargs["password"]))
            msg = "User deets are now on the server"

            user_id = str(result.inserted_id)
            acc_active = True

            # save user session
            session["user_id"] = user_id

            # save account active status for easy access later on
            session["acc_active"] = acc_active

            return json.create_acc_response_json(True, msg, user_id, acc_active)

    except ValueError as err:
        return json.create_acc_response_json(False, str(err))


@app.route("/update_acc/", methods=['POST'])
@use_kwargs(UpdateAccSchema())
@marshal_with(SuccessResponseSchema, code=200, description="Response json")
@doc(description="Endpoint for updating an existing account", tags=['Account'])
def update_account(**kwargs):
    login_failed = login_check()
    if login_failed:
        return login_failed

    succeeded = 0
    for key, value in kwargs.items():
        if key == "password":
            try:
                validate_password(kwargs["password"])

            except ValueError as err:
                return json.success_response_json(False, str(err))

        result = db.users.update_one({"_id": ObjectId(session["user_id"])},
                                     {"$set": {key: value}})
        succeeded = max(succeeded, result.modified_count)

    # bulk update message; might do individual messaging in the future
    msg = "The user's account has been updated" if succeeded else "The request was not completed. Nothing new was" \
                                                                  "passed"
    return json.success_response_json(bool(succeeded), msg)


@app.route("/delete_acc/", methods=['POST'])
@use_kwargs(UserIdSchema())
@marshal_with(SuccessResponseSchema, code=200, description="Response json")
@doc(description="Endpoint for deleting an existing account", tags=['Account'])
def delete_account(**kwargs):
    login_failed = login_check()
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
@doc(description="Endpoint for deactivating an existing account", tags=['Account'])
def deactivate_account(**kwargs):
    login_failed = login_failed = login_check()
    if login_failed:
        return login_failed
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
@doc(description="Endpoint for reactivating an existing account in a deactivated state", tags=['Account'])
def reactivate_account(**kwargs):
    login_failed = login_check()
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
@doc(description="Endpoint for creating a new account for or logging a user in through Dartmouth SSO", tags=['Account'])
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
            acc_active = result_find["acc_active"]
            name = result_find["user_info"]["name"]
            phone_num = result_find["user_info"]["phone_num"]

            # save account active status for easy access later on
            session["acc_active"] = result_find.get("acc_active")

        else:
            name = attributes.get("name")
            result_insert = db.users.insert_one(json.create_user_json(net_id_email, name))
            msg = "You've successfully created an account with DEATS through Dartmouth SSO"
            user_id = str(result_insert.inserted_id)
            acc_active = True
            phone_num = None

            # save account active status for easy access later on
            session["acc_active"] = acc_active

        # save user session
        session["user_id"] = user_id

        return json.sso_login_response_json(True,
                                            msg,
                                            user_id,
                                            acc_active,
                                            name,
                                            net_id_email,
                                            phone_num,
                                            attributes.get("isFromNewLogin"),
                                            attributes.get("authenticationDate")
                                            )


@app.route("/sso_logout/")
@marshal_with(None, code=200, description="Response json")
@doc(description="Endpoint for logging out a user logged in through Dartmouth SSO", tags=['Account'])
def sso_logout():
    login_failed = login_check()
    if login_failed:
        return login_failed

    logout_url = cas_client.get_logout_url()
    print("logout_url", logout_url)
    session.pop("user_id", default=None)
    session.pop("acc_active", default=None)

    return redirect(logout_url)


@app.route("/login/", methods=['POST'])
@use_kwargs(LoginSchema())
@marshal_with(LoginResponseSchema, code=200, description="Response json")
@doc(description="Endpoint for logging a user into an existing non-SSO account", tags=['Account'])
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
@doc(description="Endpoint for logging a user out of a non-SSO account", tags=['Account'])
def logout(**kwargs):
    login_failed = login_check()
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


@app.route("/order_del/", methods=['POST'])
@use_kwargs(OrderDelSchema())
@marshal_with(OrderDelResponseSchema, code=200, description="Response json")
@doc(description="Endpoint for ordering a delivery", tags=["Orders"])
def order_delivery(**kwargs):
    login_failed = login_check()
    if login_failed:
        return login_failed
    status_check_failed = acc_status_check()
    if status_check_failed:
        return status_check_failed

    customer = db.users.find_one({"_id": ObjectId(session["user_id"])}, {"user_info": 1, "_id": 0})
    customer["user_id"] = session["user_id"]

    order_id = db.orders.insert_one(
        json.order_delivery_json(customer,
                                 kwargs["order"]["pickup_loc"], kwargs["order"]["drop_loc"],
                                 kwargs["order"]["GET_code"])).inserted_id

    if order_id:
        msg = "The order request has been created successfully"

    else:
        msg = "The request data looks good but the order wasn't created. Try again"

    return json.order_delivery_response_json(bool(order_id), msg, str(order_id))


@app.route("/update_order/", methods=['POST'])
@use_kwargs(UpdateOrderSchema())
@marshal_with(SuccessResponseSchema, code=200, description="Response json")
@doc(description="Endpoint for updating an existing order", tags=['Orders'])
def update_order(**kwargs):
    login_failed = login_check()
    if login_failed:
        return login_failed
    status_check_failed = acc_status_check()
    if status_check_failed:
        return status_check_failed

    succeeded = 0
    order_id = kwargs["order"]["order_id"]
    msg = "The order with id, " + order_id + ", doesn't exist"
    for key, value in kwargs["order"].items():
        if key != "order_id":
            print("key: ", key, " value: ", value)
            result = db.orders.update_one({"_id": ObjectId(order_id)}, {"$set": {key: value}})

            if not result.matched_count:  # return immediately if the order doesn't exist
                return json.success_response_json(bool(succeeded), msg)

            succeeded = max(succeeded, result.modified_count)

    msg = "The user's order has been updated" if succeeded else "The request wasn't successful. No new info was " \
                                                                "provided"
    return json.success_response_json(bool(succeeded), msg)


@app.route("/make_del/", methods=['POST'])
@use_kwargs(MakeDelSchema())
@marshal_with(StartDelResponseSchema, code=200, description="Response json")
@doc(description="Endpoint for requesting to make a delivery", tags=['Orders'])
def make_delivery(delivery, **kwargs):
    login_failed = login_check()
    if login_failed:
        return login_failed
    status_check_failed = acc_status_check()
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
@doc(description="Endpoint for getting the current deliverer for an existing order", tags=['Orders'])
def get_my_deliverer(**kwargs):
    login_failed = login_check()
    if login_failed:
        return login_failed
    status_check_failed = acc_status_check()
    if status_check_failed:
        return status_check_failed

    deliverer_info = db.orders.find_one({"_id": ObjectId(kwargs["order_id"])}, {"deliverer.deliverer_info": 1, "_id": 0})

    print("deliverer_info:", deliverer_info)

    if deliverer_info is not None:
        succeeded = True
        msg = "Deliverer found!" if len(deliverer_info) else "No deliverer for this order yet. Check again later"

    else:
        succeeded = False
        msg = "The order with id, " + kwargs["order_id"] + ", doesn't exist"

    return json.get_my_deliverer_response(succeeded, msg, deliverer_info)


@app.route("/order_status/", methods=['POST'])
@use_kwargs(UserIdOrderIdSchema())
@marshal_with(GetOrderStatusResponseSchema, code=200, description="Response json")
@doc(description="Endpoint for getting the order status of an existing order", tags=['Orders'])
def get_order_status(**kwargs):
    login_failed = login_check()
    if login_failed:
        return login_failed
    status_check_failed = acc_status_check()
    if status_check_failed:
        return status_check_failed

    order_status = db.orders.find_one({"_id": ObjectId(kwargs["order_id"])}, {"order_status": 1, "_id": 0})

    if order_status:
        succeeded = True
        msg = "Request successful"

    else:
        succeeded = True
        msg = "Request unsuccessful. Try again later"

    return json.make_get_order_status_response(succeeded, msg, order_status)


@app.route("/match/", methods=['POST'])
@use_kwargs(MatchOrderSchema())
@marshal_with(MatchResponseSchema, code=200, description="Response json")
@doc(description="Endpoint for matching a deliverer with an existing order", tags=['Orders'])
def match(**kwargs):
    login_failed = login_check()
    if login_failed:
        return login_failed

    status_check_failed = status_check_failed = acc_status_check()
    if status_check_failed:
        return status_check_failed
    if status_check_failed:
        return status_check_failed

    # Check if the order exists
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
        msg = "The order with id, " + kwargs["order_id"] + ", has been canceled by the customer"
        return json.match_response_json(False, msg, None)

    result = db.orders.update_one(json.match_order_filter_json(ObjectId(kwargs["order_id"])),
                                  {"$set": json.match_unmatch_customer_json(session["user_id"], kwargs["user_info"])}, )

    customer = order["customer"]
    if result.modified_count:
        msg = "Request completed. You've been matched with the customer on the order"

    elif order["deliverer"]["user_id"] == session["user_id"]:
        msg = "You've already matched with the customer on this order"

    else:
        msg = "Request not completed. The customer on the order has already been matched with someone else"
        customer = None

    # Returns the current user info of the customer in case they updated their info before the match
    return json.match_response_json(bool(result.modified_count), msg, customer)


@app.route("/unmatch/", methods=['POST'])
@use_kwargs(UserIdOrderIdSchema())
@marshal_with(SuccessResponseSchema, code=200, description="Response json")
@doc(description="Endpoint for un-matching a deliverer from an existing order", tags=['Orders'])
def unmatch(**kwargs):
    login_failed = login_check()
    if login_failed:
        return login_failed
    status_check_failed = acc_status_check()
    if status_check_failed:
        return status_check_failed

    # Check if the order exists
    order = db.orders.find_one({"_id": (ObjectId(kwargs["order_id"]))})
    if not order:
        msg = "The order with id, " + kwargs["order_id"] + ", doesn't exist"
        return json.success_response_json(False, msg)

    # if order["customer"]["user_id"] == session["user_id and (kwargs["order_status"] != "matched" or )

    # Ensure the deliverer can be unmatched from the order
    # Customers can unmatch a deliverer from an order only if the order is not canceled and not past pending
    if order["customer"]["user_id"] == session["user_id"] and order["order_status"] != "pending":
        if order["order_status"] == "canceled":
            msg = "The request was unsuccessful. The order was canceled"

        else:
            msg = "You can't unmatch the deliverer, they're on their way"

        return json.success_response_json(False, msg)

    result = db.orders.update_one(
        json.unmatch_order_filter_json(ObjectId(kwargs["order_id"]), session["user_id"]),
        {"$set": json.match_unmatch_customer_json(order_status="pending")}, )

    if result.modified_count:
        msg = "Request completed. Order with id, " + kwargs["order_id"] + " is back to pending status"

    else:
        msg = "The request was unsuccessful. The order did not have a deliverer to unmatch from"

    return json.success_response_json(bool(result.modified_count), msg)


@app.route("/cancel_order/", methods=['POST'])
@use_kwargs(UserIdOrderIdSchema())
@marshal_with(SuccessResponseSchema, code=200, description="Response json")
@doc(description="Endpoint for canceling an existing order. Accessible to only the order creator", tags=['Orders'])
def cancel_order(**kwargs):
    login_failed = login_check()
    if login_failed:
        return login_failed
    status_check_failed = acc_status_check()
    if status_check_failed:
        return status_check_failed

    # Check if the order exists
    order = db.orders.find_one({"_id": (ObjectId(kwargs["order_id"]))})
    if not order:
        msg = "The order with id, " + kwargs["order_id"] + ", doesn't exist"
        return json.success_response_json(False, msg)

    # Ensure the user has permission to cancel the order
    if order["customer"]["user_id"] != session["user_id"]:
        msg = "You don't have permission to cancel this order"
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
        json.cancel_order_filter_json(ObjectId(kwargs["order_id"]), session["user_id"]),
        {"$set": json.match_unmatch_customer_json(order_status="canceled")}, )

    if result.modified_count:  # Check for order cancellation
        msg = "Request completed. Order with id, " + kwargs["order_id"] + " has been canceled"

    else:
        msg = "Request unsuccessful"

    return json.success_response_json(bool(result.modified_count), msg)


@app.route("/orders/", methods=['POST'])
@use_kwargs(UserIdSchema())
@marshal_with(GetOrdersResponseSchema, code=200, description="Response json")
@doc(description="Endpoint for getting all existing orders", tags=['Orders'])
def show_orders(**kwargs):
    login_failed = login_check()
    if login_failed:
        return login_failed

    cursor = db.orders.find(json.show_orders_input_json(session["user_id"]))

    return json_util.dumps(json.show_orders_response_json(cursor))


@app.route("/deliveries/", methods=['POST'])
@use_kwargs(UserIdSchema())
@marshal_with(GetDeliveriesResponseSchema, code=200, description="Response json")
@doc(description="Endpoint for getting all existing deliveries", tags=['Orders'])
def show_deliveries(**kwargs):
    login_failed = login_check()
    if login_failed:
        return login_failed

    cursor = db.orders.find(json.show_deliveries_input_json(session["user_id"]))

    return json_util.dumps(json.show_deliveries_response_json(cursor))


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
docs.register(match)
docs.register(unmatch)
docs.register(cancel_order)
docs.register(show_orders)
docs.register(show_deliveries)
