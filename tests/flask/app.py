from flask import Flask, jsonify, request
from bson.objectid import ObjectId
from logic.customer_finder import CustomerFinder

# from markupsafe import escape

import os
import pymongo
import tests.flask.user_json as user_json

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
        result = db.users.insert_one(user_json.create_user_json(data["email"], data["password"], data["name"], data["phone_num"]))
        msg = "User deets are now on the server"
        return user_json.create_acc_response_json(True, msg, str(result.inserted_id))

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
    
    if data:
        user = db.users.find_one({"email" : data["email"]})
        print("email_check", user)          
        if not user:
            msg = "The email provided does not exist on the server"

        else:
            user = db.users.find_one({"email" : data["email"], "password" : data["password"]})
            print("password_check", user)
            if not user:
                msg = "Email exists but the password provided doesn't match what's on the server" 

            else:
                print(user)
                succeeded = True
                msg = "Yayy, the user exists!"
                id = str(user["_id"])
                name = user["name"]
                phone_num = user["phone_num"]

    return user_json.login_response_json(succeeded, msg, id, name, phone_num)

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
            {"$set": user_json.request_delivery_json(data["fin_location"], data["res_location"])},)
        print("modified: ", result.modified_count, " number of customers")

        # ensure one-to-one delivery-customer matching
        cursor = db.users.find({"user_type": "D", "active": True, "matched": None})

        return user_json.success_response_json(bool(result.modified_count))
        
@app.route("/start_del/", methods=['POST'])
def start_delivery():
    data = request.get_json()

    if data:
        print("data", data)
        print(request.headers['Content-Type'])
        result = db.users.update_one({"_id": ObjectId(data["id"])},
            {"$set": user_json.start_delivery_json(data["fin_location"])},)
        print("modified: ", result.modified_count, " number of deliverers")
        
        customer_finder = CustomerFinder(data["fin_location"],
            db.users.find({"user_type": "C", "active": True, "matched": None}))

        customer_finder.sort_customers()
        
        return user_json.start_delivery_response_json(customer_finder.get_k_least_score_customers(data["num"]))

@app.route("/match/", methods=['POST'])
def match():
    data = request.get_json()

    if data:
        print("data", data)
        print(request.headers['Content-Type'])
        result = db.users.update_one({"_id": ObjectId(data["matched_id"])},
            {"$set": user_json.match_customer_json(data["id"])},)
        print("modified: ", result.modified_count, " number of customers")

        return user_json.success_response_json(bool(result.modified_count))

@app.route("/unmatch/", methods=['POST'])
def unmatch():
    data = request.get_json()

    if data:
        print("data", data)
        print(request.headers['Content-Type'])
        result = db.users.update_one({"_id": ObjectId(data["matched_id"])},
            {"$set": user_json.match_customer_json(None)},)
        print("modified: ", result.modified_count, " number of customers")

        return user_json.success_response_json(bool(result.modified_count))
    
