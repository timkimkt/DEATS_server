import pymongo
import tests.flask.user_json as user_json

from bson.objectid import ObjectId
from flask import Flask, request
from logic.customer_finder import CustomerFinder
from tests.flask.helper_functions import validate_password
from tests.flask.validate_email import validate_email

DATABASE_URL = f'mongodb+srv://db:db@cluster0.ixijz.mongodb.net/?retryWrites=true&w=majority'
client = pymongo.MongoClient(DATABASE_URL)
db = client.test1
app = Flask(__name__)
g_count = 0


@app.route("/create_acc/", methods=['POST'])
def create_account():
    data = request.get_json()

    if data:
        print("data", data)
        print(request.headers['Content-Type'])

        try:
            if data["email"]:
                valid_email = validate_email(data["email"])

                if data["password"]:
                    # strong password creation is a pain, so allow developers to test without password validation
                    if not data["test"]:
                        validate_password(data["password"])
                    result = db.users.insert_one(
                        user_json.create_user_json(valid_email.email, data["password"], data.get("name"),
                                                   data.get("phone_num")))
                    msg = "User deets are now on the server"
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
            msg = "No user id provided. The server needs to know the id of the user who's info you want to update"

    return user_json.success_response_json(succeeded, msg)


@app.route("/delete_acc/", methods=['POST'])
def delete_account():
    data = request.get_json()

    if data:
        print("data", data)
        print(request.headers['Content-Type'])
        result = db.users.delete_one({"_id": ObjectId(data["id"])})
        print(result.deleted_count)
        msg = "User with id, " + data["id"] + ", has been removed from the server"
        return user_json.delete_acc_response_json(True, msg)


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
            validate_email(data["email"])
            user = db.users.find_one({"email": data["email"]})
            print("email_check", user)
            if not user:
                msg = "The Dartmouth email provided does not exist on the server"

            else:
                user = db.users.find_one({"email": data["email"], "password": data["password"]})
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
        result = db.orders.insert_one(user_json.order_delivery_json(ObjectId(data["id"]), data["pickup_loc"],
                                                                    data["drop_loc"]))
        print("modified: ", result.inserted_id, " number of customers")

        return user_json.success_response_json(bool(result.inserted_id), "Delivery requested")


@app.route("/make_del/", methods=['POST'])
def make_delivery():
    data = request.get_json()

    if data:
        print("data", data)
        print(request.headers['Content-Type'])
        result = db.users.update_one({"_id": ObjectId(data["id"])},
                                     {"$set": user_json.make_delivery_json(data["final_des"])}, )
        print("modified: ", result.modified_count, " number of deliverers")

        customer_finder = CustomerFinder(data["final_des"],
                                         db.orders.find(user_json.find_order_json()))

        customer_finder.sort_customers()

        return user_json.start_delivery_response_json(customer_finder.get_k_least_score_customers(data["num"]))


@app.route("/order_status/", methods=['POST'])
def get_order_status():
    data = request.get_json()

    if data:
        print("data", data)
        print(request.headers['Content-Type'])
        if data["order_id"]:
            result = db.orders.find(ObjectId(data["order_id"]), {"order_status": 1, "_id": 0})

            if result:
                return user_json.get_order_status_response(True, result)

            return user_json.get_order_status_response(False, result)


@app.route("/match/", methods=['POST'])
def match():
    data = request.get_json()
    msg = "Absent JSON data. Provide a valid JSON data"
    succeeded = False

    if data:
        print("data", data)
        print(request.headers['Content-Type'])
        succeeded = db.orders.update_one(user_json.match_order_json(ObjectId(data["customer_id"])),
                                         {"$set": user_json.match_customer_json(data["id"])}, ).modified_count
        print("modified: ", succeeded, " number of customers")

        if succeeded:
            msg = "Request completed. User has been matched"

        else:
            msg = "Request not completed. User has already been matched"

        print("modified: ", succeeded, " number of users")

    return user_json.success_response_json(succeeded, msg)


@app.route("/unmatch/", methods=['POST'])
def unmatch():
    data = request.get_json()
    msg = "Absent JSON data. Provide a valid JSON data"
    succeeded = False

    if data:
        print("data", data)
        print(request.headers['Content-Type'])
        succeeded = db.users.update_one(user_json.match_order_json(ObjectId(data["customer_id"])),
                                        {"$set": user_json.match_customer_json(order_status="W")}, ).modified_count
        print("modified: ", succeeded, " number of customers")

        if succeeded:
            msg = "Request completed. User has been unmatched"

        else:
            msg = "Request not completed. User has already been unmatched"

        print("modified: ", succeeded, " number of users")

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
            cursor = db.orders.find(user_json.show_orders_json(ObjectId(data["id"])))

        else:
            cursor = db.orders.find()

        return user_json.show_deliveries_response_json(str(list(cursor)))
