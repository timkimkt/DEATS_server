import redis
from cas import CASClient
from werkzeug.utils import redirect

import tests.flask.user_json as user_json

from bson.objectid import ObjectId
from datetime import timedelta
from flask import Flask, request, session, url_for
from flask_session import Session
from logic.customer_finder import CustomerFinder
from tests.flask.helper_functions import validate_password
from tests.flask.mongo_client_connection import MongoClientConnection
from tests.flask.validate_email import validate_email

db = MongoClientConnection.get_database()
app = Flask(__name__)
g_count = 0

# Secret key for cryptographically signing session cookies (in bytes)
app.secret_key = b'8&63^#J8]NIUBMCJXO_EJN'

"Load configuration"
SESSION_TYPE = "redis"
SESSION_REDIS = redis.from_url("redis://:p202d128f66a40a4c6898c7dd732e48b222138fa5d8d1061d0de35ae3e1919765@ec2-"
                               "107-21-59-180.compute-1.amazonaws.com:24529")

app.config.from_object(__name__)
Session(app)

cas_client = CASClient(
    version=3,
    service_url="https://deats-backend-test.herokuapp.com/sso_login",
    server_url="https://login.dartmouth.edu/cas/"
)


@app.route('/')
def index():
    return redirect(url_for("sso_login"))


@app.route("/create_acc/", methods=['POST'])
def create_account():
    data = request.get_json()

    if data:
        print("data", data)
        print(request.headers['Content-Type'])

        try:
            if data["email"]:
                valid_email = validate_email(data["email"])
                user = db.users.find_one({"email": valid_email.email})
                print("email_check", user)
                if user:
                    msg = "The Dartmouth email provided is taken. Log in instead if it's your account or use a " \
                          "different email address "
                    return user_json.create_acc_response_json(False, msg)

                elif data["password"]:
                    # strong password creation is a pain, so allow developers to test without password validation
                    if not data["test"]:
                        validate_password(data["password"])
                    result = db.users.insert_one(
                        user_json.create_user_json(valid_email.email, data["password"], data.get("name"),
                                                   data.get("phone_num")))
                    msg = "User deets are now on the server"

                    # save user session
                    session["id"] = str(result.inserted_id)

                    # save account active status for easy access later on
                    session["acc_active"] = True

                    return user_json.create_acc_response_json(True, msg, str(result.inserted_id))

        except ValueError as err:
            return user_json.create_acc_response_json(False, str(err))


@app.route("/update_acc/", methods=['POST'])
def update_account():
    data = request.get_json()
    msg = "Absent JSON data. Provide a valid JSON data"
    succeeded = False

    if data:
        if data["id"]:

            if session.get("id"):
                user_id = data["id"]
                del data["id"]
                succeeded = bool(db.users.update_one({"_id": ObjectId(user_id)},
                                                     {"$set": data}).modified_count)

                if succeeded:
                    msg = "The user's info has been updated successfully"

                else:
                    msg = "The user's info wasn't updated. The change already exist"

                print("modified: ", succeeded, " number of users")

            else:
                msg = "Request denied. You're not logged in on this device"
                return user_json.request_denied_json_response(msg)

        else:
            msg = "No user id provided. The server needs to know the id of the user who's info you want to update"

    return user_json.success_response_json(succeeded, msg)


@app.route("/delete_acc/", methods=['POST'])
def delete_account():
    data = request.get_json()

    if data:
        if not session.get("id"):
            msg = "Request denied. You're not logged in on this device"
            return user_json.request_denied_json_response(msg)

        print("data", data)
        print(request.headers['Content-Type'])
        result = db.users.delete_one({"_id": ObjectId(data["id"])})
        if result.deleted_count:
            msg = "User with id, " + data["id"] + ", has been removed from the server"

        else:
            msg = "Request unsuccessful. No user with id, " + data["id"] + ", exists on the server"
        return user_json.delete_acc_response_json(bool(result.deleted_count), msg)


@app.route("/deactivate_acc/", methods=['POST'])
def deactivate_account():
    data = request.get_json()

    if data:
        print("data", data)
        print(request.headers['Content-Type'])
        result = db.users.update_one({"_id": ObjectId(data["id"])},
                                     {"$set": {"acc_active": False}}, )

        print("reactivate_acc result:", result.raw_result)
        if not result.matched_count:
            msg = "The account with id, " + data["id"] + ", does not exist on the server"

        elif result.modified_count:
            msg = "User with id, " + data["id"] + ", has been deactivated on the server"

        else:
            msg = "The account for user with id, " + data["id"] + ", is already deactivated"

        return user_json.account_status_response_json(bool(result.modified_count), msg)


@app.route("/reactivate_acc/", methods=['POST'])
def reactivate_account():
    data = request.get_json()

    if data:
        print("data", data)
        print(request.headers['Content-Type'])

        result = db.users.update_one({"_id": ObjectId(data["id"])},
                                     {"$set": {"acc_active": True}}, )
        print("reactivate_acc result:", result.raw_result)
        if not result.matched_count:
            msg = "The account with id, " + data["id"] + ", does not exist on the server"

        elif result.modified_count:
            msg = "User with id, " + data["id"] + ", has been reactivated on the server"

        else:
            msg = "The account for user with id, " + data["id"] + ", is already active"

        return user_json.account_status_response_json(bool(result.modified_count), msg)


@app.route('/sso_login/')
def sso_login():
    next = request.args.get('next')
    service_ticket = request.args.get("ticket")

    print("next", next)
    print(("tick", service_ticket))

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

    msg = "Dartmouth SSO login was successful through " \
          + ("new server login" if attributes else "stored valid TGT in user TGC cookie")
    return user_json.sso_login_response_json(True,
                                             msg,
                                             attributes.get("isFromNewLogin"),
                                             attributes.get("authenticationDate"),
                                             attributes.get("netid"),
                                             attributes.get("name"))


@app.route('/login/', methods=['POST'])
def login():
    data = request.get_json()
    print("data", data)
    print(request.headers['Content-Type'])

    succeeded = False
    msg = "Empty credentials"
    id = None
    name = None
    phone_num = None

    try:
        if data["email"]:
            valid_email = validate_email(data["email"])
            user = db.users.find_one({"email": valid_email.email})
            print("email_check", user)
            if not user:
                msg = "The Dartmouth email provided does not exist on the server"

            else:
                user = db.users.find_one({"email": valid_email.email, "password": data["password"]})
                print("password_check", user)
                if not user:
                    msg = "The provided Dartmouth email exists but the password doesn't match what's on the server"

                else:
                    print(user)
                    succeeded = True
                    msg = "Yayy, the user exists!"
                    id = str(user["_id"])
                    name = user["name"]
                    phone_num = user["phone_num"]

                    # save user session
                    session["id"] = id

                    # save account active status for easy access later on
                    session["acc_active"] = user.get("acc_active")

        return user_json.login_response_json(succeeded, msg, id, name, phone_num)

    except ValueError as err:
        return user_json.create_acc_response_json(False, str(err))


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
def order_delivery():
    data = request.get_json()

    if data:
        print("data", data)
        print(request.headers['Content-Type'])

        if session.get("id"):
            # This logic is used to make the server backward compatible
            print(session.get("acc_active"))
            if session.get("acc_active") is not None and session.get("acc_active") is False:
                msg = "Request denied. You've deactivated your account " \
                      "You have to reactivate before making this request"
                return user_json.request_denied_json_response(msg)

            result = db.orders.insert_one(
                user_json.order_delivery_json(data["id"], data["pickup_loc"], data["drop_loc"],
                                              data["pickup_loc_name"], data["drop_loc_name"]))
            print("modified: ", result.inserted_id, " number of customers")

            return user_json.order_delivery_response_json(bool(result.inserted_id), str(result.inserted_id))

        msg = "Request denied. You're not logged in on this device"
        return user_json.request_denied_json_response(msg)


@app.route("/make_del/", methods=['POST'])
def make_delivery():
    data = request.get_json()

    if data:
        print("data", data)
        print(request.headers['Content-Type'])

        if session.get("id"):
            # This logic is used to make the server backward compatible
            print(session.get("acc_active"))
            if session.get("acc_active") is not None and session.get("acc_active") is False:
                msg = "Request denied. You've deactivated your account " \
                      "You have to reactivate before making this request"
                return user_json.request_denied_json_response(msg)

            result = db.users.update_one({"_id": ObjectId(data["id"])},
                                         {"$set": user_json.make_delivery_json(data["final_des"])}, )
            print("modified: ", result.modified_count, " number of deliverers")

            customer_finder = CustomerFinder(data["final_des"],
                                             db.orders.find(user_json.find_order_json()))

            customer_finder.sort_customers()

            return user_json.start_delivery_response_json(customer_finder.get_k_least_score_customers(data["num"]))

        msg = "Request denied. You're not logged in on this device"
        return user_json.request_denied_json_response(msg)


@app.route("/my_deliverer/", methods=['POST'])
def get_my_deliverer():
    data = request.get_json()

    if data:
        print("data", data)
        print(request.headers['Content-Type'])

        if session.get("id"):
            # This logic is used to make the server backward compatible
            print(session.get("acc_active"))
            if session.get("acc_active") is not None and session.get("acc_active") is False:
                msg = "Request denied. You've deactivated your account " \
                      "You have to reactivate before making this request"
                return user_json.request_denied_json_response(msg)

            if data["order_id"]:
                deliverer = db.orders.find_one({"_id": ObjectId(data["order_id"])}, {"deliverer_id": 1, "_id": 0})

                if deliverer:
                    print("deliverer", deliverer)

                    if deliverer["deliverer_id"]:
                        deliverer["deliverer_info"] = db.users.find_one({"_id": ObjectId(deliverer["deliverer_id"])},
                                                                        {"name": 1, "email": 1, "phone_num": 1,
                                                                         "_id": 0})

                    print("deliverer_info", deliverer)

                    return user_json.make_get_my_deliverer_response(deliverer, True)

                return user_json.make_get_my_deliverer_response({}, False)

        msg = "Request denied. You're not logged in on this device"
        return user_json.request_denied_json_response(msg)


@app.route("/order_status/", methods=['POST'])
def get_order_status():
    data = request.get_json()

    if data:
        print("data", data)
        print(request.headers['Content-Type'])

        if session.get("id"):
            # This logic is used to make the server backward compatible
            print(session.get("acc_active"))
            if session.get("acc_active") is not None and session.get("acc_active") is False:
                msg = "Request denied. You've deactivated your account " \
                      "You have to reactivate before making this request"
                return user_json.request_denied_json_response(msg)

            if data["order_id"]:
                result = db.orders.find_one({"_id": ObjectId(data["order_id"])}, {"order_status": 1, "_id": 0})

                if result:
                    user_json.make_get_order_status_response(result, True)

                else:
                    result = {}
                    user_json.make_get_order_status_response(result, False)

                return result

        msg = "Request denied. You're not logged in on this device"
        return user_json.request_denied_json_response(msg)


@app.route("/match/", methods=['POST'])
def match():
    data = request.get_json()
    msg = "Absent JSON data. Provide a valid JSON data"
    succeeded = False

    if data:
        print("data", data)
        print(request.headers['Content-Type'])

        if session.get("id"):
            # This logic is used to make the server backward compatible
            print(session.get("acc_active"))
            if session.get("acc_active") is not None and session.get("acc_active") is False:
                msg = "Request denied. You've deactivated your account " \
                      "You have to reactivate before making this request"
                return user_json.request_denied_json_response(msg)

            succeeded = db.orders.update_one(user_json.match_order_json(ObjectId(data["order_id"])),
                                             {"$set": user_json.match_customer_json(data["id"])}, ).modified_count
            print("modified: ", succeeded, " number of customers")

            if succeeded:
                msg = "Request completed. User has been matched"

            else:
                msg = "Request not completed. User has already been matched"

            print("modified: ", succeeded, " number of users")

        else:
            msg = "Request denied. You're not logged in on this device"
            return user_json.request_denied_json_response(msg)

    return user_json.success_response_json(succeeded, msg)


@app.route("/unmatch/", methods=['POST'])
def unmatch():
    data = request.get_json()
    msg = "Absent JSON data. Provide a valid JSON data"
    succeeded = False

    if data:
        print("data", data)
        print(request.headers['Content-Type'])

        if session.get("id"):
            # This logic is used to make the server backward compatible
            print(session.get("acc_active"))
            if session.get("acc_active") is not None and session.get("acc_active") is False:
                msg = "Request denied. You've deactivated your account " \
                      "You have to reactivate before making this request"
                return user_json.request_denied_json_response(msg)

            succeeded = db.users.update_one(user_json.match_order_json(ObjectId(data["customer_id"])),
                                            {"$set": user_json.match_customer_json(order_status="W")}, ).modified_count
            print("modified: ", succeeded, " number of customers")

            if succeeded:
                msg = "Request completed. User has been unmatched"

            else:
                msg = "Request not completed. User has already been unmatched"

            print("modified: ", succeeded, " number of users")

        else:
            msg = "Request denied. You're not logged in on this device"
            return user_json.request_denied_json_response(msg)

    return user_json.success_response_json(succeeded, msg)


@app.route("/orders/", methods=['POST'])
def show_orders():
    data = request.get_json()
    msg = "Absent JSON data. Provide a valid JSON data"
    succeeded = False

    if data:
        print("data", data)
        print(request.headers['Content-Type'])
        if data["id"]:
            if not session.get("id"):
                msg = "Request denied. You're not logged in on this device"
                return user_json.request_denied_json_response(msg)

            cursor = db.orders.find(user_json.show_orders_json(ObjectId(data["id"])))

        else:
            cursor = db.orders.find()
            print(cursor)

        return user_json.show_orders_response_json(str(list(cursor)))


@app.route("/deliveries/", methods=['POST'])
def show_deliveries():
    data = request.get_json()
    msg = "Absent JSON data. Provide a valid JSON data"
    succeeded = False

    if data:
        print("data", data)
        print(request.headers['Content-Type'])
        if data["id"]:
            if not session.get("id"):
                msg = "Request denied. You're not logged in on this device"
                return user_json.request_denied_json_response(msg)

            cursor = db.orders.find(user_json.show_orders_json(ObjectId(data["id"])))

        else:
            cursor = db.orders.find()

        return user_json.show_deliveries_response_json(str(list(cursor)))
