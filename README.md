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

## Server Environment Setup (Re-deploying the Server)
- If you want to add changes to the app server and/or deploy it to a different site address (i.e. **not the official or D&T site address**), either locally or remotely, follow the instructions below.

- **Note**: Only developers can remotely deploy new edits to the official or D&T hosting address.  

#### Intial Setup
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
2.Confirm that the environment is activated: your shell prompt should show the name of the activated environment. **Note**: virtual environments are healthy for your Python projects. They are the way to go! You can find Python's official documentation for creating and activating virtual environments [here](https://docs.python.org/3/library/venv.html).
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
