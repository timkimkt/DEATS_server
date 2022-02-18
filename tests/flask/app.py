from flask import Flask
from flask import request

# from markupsafe import escape

import os
import pymongo

DATABASE_URL = f'mongodb+srv://db:db@cluster0.ixijz.mongodb.net/?retryWrites=true&w=majority'

client = pymongo.MongoClient(DATABASE_URL)
db = client.test

app = Flask(__name__)


@app.route("/create_acc/", methods=['POST'])
def create_account():
    data = request.get_json()
    print("data", data)
    print(request.headers['Content-Type'])
    result = db.users.insert_one(data)
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
    print(request.headers['Content-Type'])
    cursor = db.users.find({})
    return str(list(cursor))
    

    
