from flask import Flask
from flask_socketio import SocketIO
from flask_cors import CORS
from flasgger import Swagger
from flask_mqtt import Mqtt
import eventlet

# Initial Flask application
app = Flask(__name__)

# Threaded
eventlet.monkey_patch() 
# Define web api docs
app.config['SWAGGER'] = {
    'title': 'iVIT-T',
    'uiversion': 3
}

swagger = Swagger(app)
CORS(app, supports_credentials=True)
socketio = SocketIO(app, cors_allowed_origins='*')
app.config['JSON_SORT_KEYS'] = False
mqtt = Mqtt()