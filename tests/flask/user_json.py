# ------------- Inputs for MongoDB ------------- #
def create_user_json(email, password, name=None, phone_num=None):
    return {
            "email" : email,
            "name" : name,
            "password" : password,
            "phone_num" : phone_num,
            "user_type" : None,
            "active" : False,
            "matched" : None,
            "fin_location" : {
                "x" : None, 
                "y" : None
            },
            "res_location" : {
                "x" : None, 
                "y" : None
            }
        }

def request_delivery_json(fin_location, res_location):
    return {
            "user_type" : 'C',
            "active" : True,
            "fin_location" : fin_location,
            "res_location" : res_location
        }

# temporarily assume final location and current location are the same
def start_delivery_json(fin_location):
    return {
            "user_type" : 'D',
            "active" : True,
            "fin_location" : fin_location
        }

def match_customer_json(deliver_id):
    return {
            "matched" : deliver_id
        }

# ------------- JSON responses ------------- #
def login_response_json(succeeded, msg, id, name, phone_num):
    return {
            "succeeded" : succeeded,
            "msg" :msg,
            "id" : id,
            "name" : name,
            "phone_num" : phone_num
        }

def create_acc_response_json(succeeded, msg, user_id):
    return {
            "succeeded" : succeeded,
            "msg" : msg,
            "user_id" :user_id,
        }

def delete_acc_response_json(succeeded, msg):
    return {
            "succeeded" : succeeded,
            "msg" : msg,
        }

def start_delivery_response_json(unmatched_customers):
    return {
            "unmatched_customers" : unmatched_customers
        }

def success_response_json(succeeded):
    return {
            "succeeded" : succeeded
        }

def show_users_response_json(registered_users):
    return {
            "registered_users" : registered_users
        }

def global_count_response_json(global_count):
    return {
            "global count" : global_count
        }

        


