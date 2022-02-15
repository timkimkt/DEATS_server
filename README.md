# DEATS_server

# Deployment
Currently deploying automatically to [heroku](https://d-eats-backend.herokuapp.com/)

# Server environment setup
1. be sure [node.js](https://nodejs.org/en/download/) has been installed
2. run
```
brew uninstall --force mongodb
```
```
brew tap mongodb/brew
```
```
brew install mongodb-community
```
* issues ran into: no taps
solved using 
```
brew tap homebrew/bundle
```
```
brew update
```
```
brew install mongodb/brew/mongodb-community
```
if already installed: 
```
brew reinstall mongodb-community
```
run:
```
brew services start mongodb/brew/mongodb-community
```
3. run 
```
mongo
```
to be running the mongoshell