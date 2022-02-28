import pymongo
import tests.flask.user_json as user_json

from bson.objectid import ObjectId
from flask import Flask, request
from logic.customer_finder import CustomerFinder
from tests.flask.helper_functions import validate_password
from tests.flask.validate_email import validate_email

DATABASE_URL = f'mongodb+srv://db:db@cluster0.ixijz.mongodb.net/?retryWrites=true&w=majority'
client = pymongo.MongoClient(DATABASE_URL)
db = client.test
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


@app.route("/request_del/", methods=['POST'])
def request_delivery():
    data = request.get_json()

    if data:
        print("data", data)
        print(request.headers['Content-Type'])
        result = db.users.update_one({"_id": ObjectId(data["id"])},
                                     {"$set": user_json.request_delivery_json(data["fin_location"],
                                                                              data["res_location"])}, )
        print("modified: ", result.modified_count, " number of customers")

        # ensure one-to-one delivery-customer matching
        # cursor = db.users.find({"user_type": "D", "active": True, "matched": None})

        return user_json.success_response_json(bool(result.modified_count), "Delivery requested")


@app.route("/start_del/", methods=['POST'])
def start_delivery():
    data = request.get_json()

    if data:
        print("data", data)
        print(request.headers['Content-Type'])
        result = db.users.update_one({"_id": ObjectId(data["id"])},
                                     {"$set": user_json.start_delivery_json(data["fin_location"])}, )
        print("modified: ", result.modified_count, " number of deliverers")

        customer_finder = CustomerFinder(data["fin_location"],
                                         db.users.find({"user_type": "C", "active": True, "matched": None}))

        customer_finder.sort_customers()

        return user_json.start_delivery_response_json(customer_finder.get_k_least_score_customers(data["num"]))


@app.route("/match/", methods=['POST'])
def match():
    data = request.get_json()
    msg = "Absent JSON data. Provide a valid JSON data"
    succeeded = False

    if data:
        print("data", data)
        print(request.headers['Content-Type'])
        succeeded = db.users.update_one({"_id": ObjectId(data["matched_id"])},
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
        succeeded = db.users.update_one({"_id": ObjectId(data["matched_id"])},
                                        {"$set": user_json.match_customer_json(None)}, ).modified_count
        print("modified: ", succeeded, " number of customers")

        if succeeded:
            msg = "Request completed. User has been unmatched"

        else:
            msg = "Request not completed. User has already been unmatched"

        print("modified: ", succeeded, " number of users")

    return user_json.success_response_json(succeeded, msg)
