from flask import Flask
from flask_socketio import SocketIO
from flask_cors import CORS
from flasgger import Swagger
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
CORS(app)
socketio = SocketIO(app, cors_allowed_origins=['http://127.0.0.1/', "https://127.0.0.1/"])
app.config['JSON_SORT_KEYS'] = False