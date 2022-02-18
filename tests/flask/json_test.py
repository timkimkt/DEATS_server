from flask import Flask
from flask import request

# from markupsafe import escape

import os

app_json = Flask(__name__)
users = ['edmund', 'jeff', 'kathy', 'brian', 'tim']

@app_json.route('/json/mywords/', methods=['POST'])
def show_user_words():
    data = request.get_json()

    if data:
        if 'words' in data:
            return data['words']
        
        return "Error: JSON object has no 'words' key"
    
    return "Error: JSON object has no keys"

@app_json.route('/json', methods=['POST'])
@app_json.route('/json/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if data:
        if 'email' in data:
            email = data['email']

            if 'password' in data:
                password = data['password']

                split_email = email.split('@')
                if validate_user_creds(split_email, request.form['pass']):
                    return '''
                            User: {} exists
                            and
                            Password ending in ...{} was validated as correct
                            '''.format(split_email[0], split_email[1][len(split_email[1])-3:])

                return "Wrong email \n or \n password!"

            return "Error: JSON object has no password key"

        return "Error: JSON object has no email key AND/OR password key"

    return "Error: JSON object has no keys"

def validate_user_creds(split_email, password):
    if len(split_email) < 2:
        return False
    
    return split_email[0] in users and split_email[1] == 'deats.com' and password == 'thebest'
