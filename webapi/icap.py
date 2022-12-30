from flask import Blueprint, request, jsonify
from flasgger import swag_from
from .common.utils import handle_exception, exists, read_json, success_msg, error_msg
from .common.config import YAML_MAIN_PATH
from .common.thingsboard import init_for_icap
from webapi import app
import logging

app_icap = Blueprint( 'icap', __name__)
# Define API Docs path and Blue Print
YAML_PATH       = YAML_MAIN_PATH + "/icap"

@app_icap.route("/icap_status/", methods=['GET'])
def icap_status():
    return jsonify(
                    {
                        "ICAP_STATUS":app.config["ICAP_STATUS"],
                        "TB_CREATE_TIME":app.config["TB_CREATE_TIME"],
                        "TB_DEVICE_ID":app.config["TB_DEVICE_ID"],
                        "TB_TOKEN": app.config["TB_TOKEN"]
                    }
                )

@app_icap.route("/icap/addr/", methods=['GET'])
@swag_from("{}/{}".format(YAML_PATH, "get_addr.yml"))
def get_addr():
    return jsonify({"address":"{}:{}".format(app.config["TB"], app.config["TB_PORT"])}), 200

@app_icap.route("/icap/addr/", methods=['PUT'])
@swag_from("{}/{}".format(YAML_PATH, "put_addr.yml"))
def put_addr():
    ADDR_KEY = "address"

    # Get data: support form data and json
    data = dict(request.form) if bool(request.form) else request.get_json()

    if data is None:
        logging.info('Using default address: "{}:{}"'.format(
            app.config.get("TB"), app.config.get("TB_PORT")
        ))
    else:
        new_addr = data.get(ADDR_KEY)
        if new_addr is None:
            msg = "Unexcepted data, make sure the key is {} ... ".format(ADDR_KEY)
            logging.error(msg); 
            return jsonify(msg), 400
        
        ip,port = new_addr.split(':')
        app.config.update({
            "TB": ip,
            "TB_PORT": port 
        })
        
    try:
        if(init_for_icap()):
            # register_mqtt_event()
            return jsonify( app.config.get('TB_DEVICE_ID') ), 200
        else:
            return jsonify( 'Connect to iCAP ... Failed' ), 400

    except Exception as e:
        return jsonify( handle_exception(e) ), 400

@app_icap.route("/icap/get_device_id/", methods=['GET'])
@swag_from("{}/{}".format(YAML_PATH, "get_device_id.yml"))
def get_tb_id():
    return jsonify( app.config.get('TB_DEVICE_ID') ), 200