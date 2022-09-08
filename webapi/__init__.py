from flask import Flask
from flask_socketio import SocketIO
from flask_cors import CORS
from flasgger import Swagger
import eventlet

# initial Flask application
app = Flask(__name__)

eventlet.monkey_patch() # Threaded
swagger = Swagger(app)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins='*')
app.config['JSON_SORT_KEYS'] = False