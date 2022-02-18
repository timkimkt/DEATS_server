from flask import Flask
from flask import request
from flask import render_template

from markupsafe import escape

import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.path.join('static')
users = ['edmund', 'jeff', 'kathy', 'brian', 'tim']

@app.route('/mywords/<path:words>')
def show_user_words(words):
    return f'{escape(words)}'

@app.route('/', methods=['POST', 'GET'])
@app.route('/login', methods=['POST', 'GET'])
def login():
    error = ''
    root_folder = app.config['UPLOAD_FOLDER']
    if request.method == 'POST':
        name = request.form['email'].split('@')[0]
        if validate_user_creds(name,
                       request.form['pass']):
            return login_helper(name, root_folder)
        else:
            error = 'Wrong email \n or \n password!'

    return render_template('login.html', error=error, root_folder=root_folder)

def validate_user_creds(name, password):
    return name in users and password == 'thebest'

def login_helper(name, root_folder):
    return render_template('hello.html', name=name, root_folder=root_folder)
    
