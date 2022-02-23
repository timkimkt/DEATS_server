from flask import Flask
from flask import request
from bson.objectid import ObjectId

# from markupsafe import escape

import os
import pymongo
import tests.flask.user_json as user_json

DATABASE_URL = f'mongodb+srv://db:db@cluster0.ixijz.mongodb.net/?retryWrites=true&w=majority'

client = pymongo.MongoClient(DATABASE_URL)
db = client.test

app = Flask(__name__)


@app.route("/create_acc/", methods=['POST'])
def create_account():
    data = request.get_json()

    if data:
        print("data", data)
        print(request.headers['Content-Type'])
        result = db.users.insert_one(user_json.create_user_json(data["email"], data["password"]))
        return str(result.inserted_id)

@app.route('/login/', methods=['POST'])
def login():
    data = request.get_json()
    print("data", data)
    print(request.headers['Content-Type'])
    
    if data:
        user = db.users.find_one({"email" : data["email"]})
        print("email_check", user)          
        if not user:
            return "Failed. Fix email" 

        user = db.users.find_one({"email" : data["email"], "password" : data["password"]})
        print("password_check", user)
        if not user:
            return "Failed. Fix password"

        return "Success"

    return "Empty credentials"

@app.route("/show_users/", methods=['GET'])
def show_users():
    data = request.get_json()
    print("data", data)
    #print(request.headers['Content-Type'])
    cursor = db.users.find({})
    return str(list(cursor))

@app.route("/request_del/", methods=['POST'])
def request_delivery():
    data = request.get_json()

    if data:
        print("data", data)
        print(request.headers['Content-Type'])
        result = db.users.update_one({"_id": ObjectId(data["id"])},
            {"$set": user_json.request_delivery_json(data["fin_location"], data["res_location"])},)
        return str(result.modified_count)

@app.route("/start_del/", methods=['POST'])
def start_delivery():
    data = request.get_json()

    if data:
        print("data", data)
        print(request.headers['Content-Type'])
        result = db.users.update_one({"_id": ObjectId(data["id"])},
            {"$set": user_json.start_delivery_json(data["fin_location"])},)
        return str(result.modified_count)
    
