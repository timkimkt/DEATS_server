from flask import session
import tests.flask.database_and_response_jsons as json


def login_check():
    if not session.get("user_id"):
        msg = "Request denied. This device is not logged into the server yet"
        return json.request_denied_json_response(msg)


def acc_status_check():
    if not session.get("acc_active"):
        print(session.get("acc_active"))
        msg = "Request denied. You've deactivated your account. You have to reactivate it before making this request"
        return json.request_denied_json_response(msg)
