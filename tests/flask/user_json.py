def create_user_json(email, password):
    return {
            "email" : email,
            "password" : password,
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

