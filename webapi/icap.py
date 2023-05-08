from flask import Blueprint, request, jsonify
from flasgger import swag_from
from .common.utils import handle_exception, write_json, read_json
from .common.config import YAML_MAIN_PATH, VERSION_PATH
from .common.thingsboard import init_for_icap, get_tb_info, KEY_TB_DEVICE_ID, KEY_DEVICE_TYPE, TB, TB_PORT, register_mqtt_event
from webapi import app
import logging

app_icap = Blueprint( 'icap', __name__)
# Define API Docs path and Blue Print
YAML_PATH       = YAML_MAIN_PATH + "/icap"


@app_icap.route("/get_my_ip", methods=['GET'])
@swag_from("{}/{}".format(YAML_PATH, "get_my_ip.yml"))
def get_my_ip():
    return jsonify( {'ip': request.remote_addr} ), 200

@app_icap.route("/icap/info", methods=['GET'])
@swag_from("{}/{}".format(YAML_PATH, "icap_info.yml"))
def icap_info():
    return jsonify(get_tb_info()), 200

@app_icap.route("/icap/device/id", methods=['GET'])
@swag_from("{}/{}".format(YAML_PATH, "get_device_id.yml"))
def get_device_id():
    return jsonify( { "device_id": app.config.get(KEY_TB_DEVICE_ID) } ), 200

@app_icap.route("/icap/device/type", methods=['GET'])
@swag_from("{}/{}".format(YAML_PATH, "get_device_type.yml"))
def get_device_type():
    return jsonify( { "device_type": app.config.get(KEY_DEVICE_TYPE) } ), 200

@app_icap.route("/icap/addr", methods=['GET'])
@swag_from("{}/{}".format(YAML_PATH, "get_addr.yml"))
def get_addr():
    return jsonify( { "ip" : str(app.config[TB]), "port": str(app.config[TB_PORT]) } ), 200

@app_icap.route("/icap/addr", methods=['POST'])
@swag_from("{}/{}".format(YAML_PATH, "modify_addr.yml"))
def modify_addr():

    K_IP = "ip"
    K_PORT = "port"

    # Get data: support form data and json
    data = dict(request.form) if bool(request.form) else request.get_json()

    # Check data
    if data is None:
        msg = 'Get empty data, please make sure the content include "ip" and "port". '
        logging.error(msg)        
        return jsonify(msg), 400

    # Check ip
    ip = data.get(K_IP)
    if ip is None:
        msg = "Get empty ip address ... "
        logging.error(msg); 
        return jsonify(msg), 400
    
    # Check port
    port = data.get(K_PORT)
    if port is None:
        msg = "Get empty port number ... "
        logging.error(msg); 
        return jsonify(msg), 400
    
    app.config.update({
        TB: ip,
        TB_PORT: port 
    })

    # Reading default config
    env_config = read_json(VERSION_PATH)
    # Writing config
    env_config["ICAP_HOST"] = app.config[TB]
    env_config["ICAP_PORT"] = app.config[TB_PORT]
    write_json(VERSION_PATH, env_config)
        
    try:
        if(init_for_icap()):
            register_mqtt_event()
            return jsonify( get_tb_info() ), 200
        else:
            return jsonify( 'Connect to iCAP ... Failed' ), 400

    except Exception as e:
        return jsonify( handle_exception(e) ), 400
