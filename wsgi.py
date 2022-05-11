from tests.flask.app import app, socketio
from tests.flask.json_test import app_json

if __name__ == "__main__":
    socketio.run(app)
