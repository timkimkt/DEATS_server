# DEATS Server
## About

#### Components
The DEATS app server runs on Flask's web framework and uses MongoDB Atlas for its data storage.

#### Official Hosting Site
- To make API calls to the server use the official hosting site address: ***`https://deats-server.herokuapp.com/`***.
- The official hosting site has the most stable up-to-date version of the server, albeit it might lack the lastest features in beta or development phase.
- The official hosting site is set **in sync** with code on the main branch of this repository i.e. the site hosts deployed code that has been pushed to **main only**.
- To access features in the development or beta phase, use the D&T hosting site below.

#### Development and Testing (D&T) Hosting Site
- To make API calls to the most current server in beta or development phase use the D&T hosting site address ***`https://deats-backend-test.herokuapp.com/`***.
- The D&T hosting site is meant for developers to test new features of the app before deploying to the main server, but anyone else granted permission is welcome to use it.
- Features may not be stable.


## Server Deployment & Environment Setup 
- If you want to add changes to the app server and/or deploy it to a different site address (i.e. **not the official or D&T site address**), either locally or remotely, follow the instructions below.

- **Note**: Only developers can remotely deploy new edits to the official or D&T hosting address.  

#### Initial Setup
1. The server is written mainly in Python so be sure the latest version of [Python](https://nodejs.org/en/download/) is installed on your computer.
2. Ensure the latest version of [Git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git) is installed. 
3. `Create and cd into the root folder` you wish to use for this project.
4. Execute the command: `git clone git@github.com:timkimkt/DEATS_server.git` to get a local version of the repository on your computer.

#### Deploying the Server Locally
1. Create a virtual environment folder `<venv>` and activate the environment as follows:
```
Python3 -m venv venv
. venv/bin/activate
```
2. Confirm that the environment is activated: your shell prompt should show the name of the activated environment. **Note**: virtual environments are healthy for your Python projects. They are the way to go! You can find Python's official documentation for creating and activating virtual environments [here](https://docs.python.org/3/library/venv.html).
3. Install all the server dependencies by running `pip freeze > requirements.txt`.
4. You should now have all the dependencies listed in the `requirements.txt` file installed in your virtual environment. You can confirm this by running `pip list`.
5. Run `heroku local` to deploy the app locally. The server should now be running on [http://localhost:5000](http://localhost:5000). 
6. **Note**: Running the server locally has limitations such as not being able to make cross-network calls to the server. For cross-network calls, consider deploying the server remotely as described below.

#### Deploying the Server Remotely on Heroku
1. Make sure you have a [Heroku account](https://signup.heroku.com/).
2. Install and log into the Heroku CLI by following the instructions [here](https://devcenter.heroku.com/articles/getting-started-with-python#set-up). 
3. Run `heroku create` to create the app.
4. Run `git push heroku main` to deploy the app
5. Further instructions on deploying remotely to Heroku can be found [here](https://devcenter.heroku.com/articles/getting-started-with-python#deploy-the-app).

#### Making and Pushing New Changes
1. Make all the necessary changes in the file you want.
2. Run the following commands to commit the new changes:
```
git add .
git commit -m "<commit message>"
```
or
```
git commit -am "<commit message>"
```
3. Run `git push heroku main` to deploy the new changes.
**Optional**: You don't need to do this, but to quickly understand how Flask works and how it's been used in this project you may follow Flask's quickstart guidelines [here](https://flask.palletsprojects.com/en/2.1.x/quickstart/).


## API Reference DEATS version
- A comprehensive list of the exposed endpoints for **`DEATS server 1.0.0`** is provided in this README below.
- For the most up-to-date comprehensive list of exposed endpoints for the revamped version, **`DEATS server 2.0.0`**, visit the following links.
  - mainline (prod, used by DEATS frontend): [deats-server.herokuapp.com/DEATS-server-api-ui/](https://deats-server.herokuapp.com/DEATS-server-api-ui/)
  - testline (dev, used by DEATS server developers): [d-testline.herokuapp.com/DEATS-server-api-ui/](https://d-testline.herokuapp.com/DEATS-server-api-ui/) 
- In **`DEATS server 2.0.0`**, we're making the lives of clients easier by hosting all the exposed endpoints on the server through Swagger to allow clients to get the most up-to-date API references for both mainline and testline. 
- The hosted API references are interactive. This means that users can play with the server and easily learn how to make requests to it, as well as see in realtime
  all responses returned by the server.
- After playing with an endpoint and getting the results wanted, users can just copy-paste the json object into their source code or follow the same pattern to implement it in their code.
- **Note:** Options for each endpoint are for preflight requests.


### GET Methods
###### /sso_login
>- Description: Endpoint for logging a user in through Dartmouth SSO.
>- Input: No input required
    
>- Output: Returns the following JSON object.
        {
            "succeeded": succeeded,
            "msg": msg,
            "user_id": user_id,
            "is_new_login": is_new_login,
            "authentication_date": authentication_date,
            "user_info":
                {
                    "id": id,
                    "email": net_id_email,
                    "name": name,
                    "phone_num": phone_num,
                }
        }

###### /sso_logout
>- Description: Endpoint for logging out a user through Dartmouth SSO.
>- Input: No input required
    
>- Output: No output

### POST Methods
###### /create_acc
>- Description: Endpoint for creating an account for a new user.
>- Input: Accepts the following JSON object.
        {
            "email": <email>, 
            "password": <password>, 
            "name": <name>,
            "phone_num": <phone_num>
        }
    
>- Output: Returns the following JSON object.
        {
            "succeeded": succeeded,
            "msg": msg,
            "user_id": user_id
        }
    
###### /update_acc
>- Description: Endpoint for updating an existing account.
>- Input: Accepts the following JSON object.
        {
            "id": <id>
        }
    
>- Output: Returns the following JSON object.
        {
            "succeeded": succeeded,
            "msg": msg
        }

###### /delete_acc
>- Description: Endpoint for deleting an existing account.
>- Input: Accepts the following JSON object.
        {
            "id": <id>
        }
    
>- Output: Returns the following JSON object.
        {
            "succeeded": succeeded,
            "msg": msg
        }

###### /deactivate_acc
>- Description: Endpoint for deactivating an existing account.
>- Input: Accepts the following JSON object.
        {
            "id": <id>
        }
    
>- Output: Returns the following JSON object.
        {
            "succeeded": succeeded,
            "msg": msg
        }

###### /reactivate_acc
>- Description: Endpoint for reactivating a deactivated account.
>- Input: Accepts the following JSON object.
        {
            "id": <id>
        }
    
>- Output: Returns the following JSON object.
        {
            "succeeded": succeeded,
            "msg": msg
        }

###### /login
>- Description: Endpoint for logging a user in.
>- Input: Accepts the following JSON object.
        {
            "email": <email>, 
            "password": <password>
        }
    
>- Output: Returns the following JSON object.
        {
            "succeeded": succeeded,
            "msg": msg,
            "id": id,
            "name": name,
            "phone_num": phone_num
        }

###### /logout
>- Description: Endpoint for logging a user out.
>- Input: Accepts the following JSON object.
        {
            "id": <id>
        }
    
>- Output: Returns the following JSON object.
        {
            "succeeded": succeeded,
            "msg": msg
        }

###### /order_del
>- Description: Endpoint for ordering a delivery.
>- Input: Accepts the following JSON object.
        {
            "id": <id>, 
            "pickup_loc": <password>, 
            "pickup_loc_name": <pickup_loc_name>,
            "drop_loc": <drop_loc>,
            "drop_loc_name": <drop_loc_name>
            "GET_code": <GET_code> *Optional*
        }
    
>- Output: Returns the following JSON object.
        {
            "succeeded": succeeded,
            "order_id": order_id
        }

> ###### /update_order
>- Description: Endpoint for updating any of the details of an existing order. Updates can be done in bulk or NOT.
   Just POST the keys and the new values to update them with. Updates are idempotent.
>- Input: Accepts any combination of the keys in the following JSON object.
        {
            "id": <id>, 
            "pickup_loc": <password>, 
            "pickup_loc_name": <pickup_loc_name>,
            "drop_loc": <drop_loc>,
            "drop_loc_name": <drop_loc_name>
            "GET_code": <GET_code>
        }
    
>- Output: Returns the following JSON object.
        {
            "succeeded": succeeded,
            "msg": msg
        }
        
###### /make_del
>- Description: Endpoint for starting a request to make deliveries.
>- Input: Accepts the following JSON object.
        {
            "id": <id>, 
            "final_des": <final_des>, 
            "num": <num>
        }
    
>- Output: Returns the following JSON object.
        {
            "unmatched_users": unmatched_users
        }

###### /my_deliverer
>- Description: Endpoint for checking who the deliverer of a user is.
>- Input: Accepts the following JSON object.
        {
            "order_id": <order_id>
        }
    
>- Output: Returns the following JSON object.
        {
            "succeeded": succeeded,
            "name": name,
            "email": email,
            "phone_num": phone_num
        }

###### /order_status
>- Description: Endpoint for checking the status (C: completed, F: food picked up, M: matched, W: waiting) of an order
>- Input: Accepts the following JSON object.
        {
            "order_id": <order_id>
        }
    
>- Output: Returns the following JSON object.
        {
            "succeeded": succeeded,
            "order_status": order_status
        }

###### /match
>- Description: Endpoint for matching a deliverer with a customer.
>- Input: Accepts the following JSON object.
        {
            "id": <id>,
            "order_id": order_id
        }
    
>- Output: Returns the following JSON object.
        {
            "succeeded": succeeded,
            "msg": msg
        }

###### /unmatch
>- Description: Endpoint for unmatching a deliverer from a customer or vice versa.
>- Input: Accepts the following JSON object.
        {
            "customer_id": <customer_id>
        }
    
>- Output: Returns the following JSON object.
        {
            "succeeded": succeeded,
            "msg": msg
        }

###### /orders
>- Description: Endpoint for viewing all orders made by a user.
>- Input: Accepts the following JSON object. 
        {
            "id": <id>
        }
    
>- Output: Returns the following JSON object.
        {
            "orders": orders"
        }

###### /deliveries
>- Description: Endpoint for viewing all deliveries made by a user.
>- Input: Accepts the following JSON object.
        {
            "id": <id>
        }
    
>- Output: Returns the following JSON object.
        {
            "deliveries": deliveries
        }

## References
- [Flask](https://flask.palletsprojects.com/en/2.1.x/)
- [Heroku](https://www.heroku.com/)
