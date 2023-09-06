import os, logging
from flask import Blueprint, request, jsonify, send_from_directory
from flasgger import swag_from
from pathlib import Path
from webapi import app
from .common.utils import exists,read_json, success_msg, error_msg, get_target_addr  
from .common.config import PLATFORM_CFG, ROOT, YAML_MAIN_PATH, EXPORT_LIST
from .common.export_tool import set_export_json, Convert_model, check_convert_exist, icap_upload_file, post_metadata
from .common.inspection import Check
from signal import SIGKILL

chk = Check()
app_export = Blueprint( 'export_model', __name__)
# Define API Docs path and Blue Print
YAML_PATH       = YAML_MAIN_PATH + "/export_model"

@app_export.route('/<uuid>/get_export_platform/<arch>', methods=['GET']) 
@swag_from("{}/{}".format(YAML_PATH, "get_export_platform.yml"))
def get_export_platform(uuid, arch):
    # Check uuid is/isnot in app.config["PROJECT_INFO"]
    if not ( uuid in app.config["PROJECT_INFO"].keys()):
        return error_msg(400, {}, "UUID:{} does not exist.".format(uuid), log=True)
    if not arch:
        return error_msg(400, {}, "This value of arch is null.", log=True)
    # Get platform
    platform = app.config["PROJECT_INFO"][uuid]["platform"]
    # Get all platform list
    platform_list = read_json(PLATFORM_CFG)["platform"]
    # Filter platform
    type = app.config["PROJECT_INFO"][uuid]["type"]
    if "classification" == type:
        if "xilinx" == platform:
            return success_msg(200, {"export_platform":[platform]}, "Success")
        else:
            platform = [ val for val in platform_list if val != "xilinx"]
            return success_msg(200, {"export_platform":platform}, "Success")
    elif "object_detection" == type:
        if platform != "xilinx":
            if arch == "yolov4":
                platform = [ val for val in platform_list if val != "xilinx" and val != "hailo"]
                return success_msg(200, {"export_platform":platform}, "Success")
            if arch == "yolov4-tiny":
                platform = [ val for val in platform_list if val != "xilinx"]
                return success_msg(200, {"export_platform":platform}, "Success")
        else:
            if "leaky" in arch:
                return success_msg(200, {"export_platform":["xilinx", "hailo"]}, "Success")
            if "tiny" in arch:
                return success_msg(200, {"export_platform":["xilinx"]}, "Success")
            
@app_export.route('/<uuid>/start_converting', methods=['POST']) 
@swag_from("{}/{}".format(YAML_PATH, "start_converting.yml"))
def start_converting(uuid):
    # Check uuid is/isnot in app.config["PROJECT_INFO"]
    if not ( uuid in app.config["PROJECT_INFO"].keys()):
        return error_msg(400, {}, "UUID:{} does not exist.".format(uuid), log=True)
    # Check key of front
    if not "iteration" in request.get_json().keys():
        return error_msg(400, {}, "KEY:iteration does not exist.", log=True)
    if not "export_platform" in request.get_json().keys():
        return error_msg(400, {}, "KEY:export_platform does not exist.", log=True)
    # Get project name
    prj_name = app.config["PROJECT_INFO"][uuid]["project_name"]
    # Get type
    type = app.config["PROJECT_INFO"][uuid]["type"]
    # Get export_platform (Get value of front)
    export_platform = request.get_json()['export_platform']
    front_iteration = request.get_json()['iteration']
    # Mapping iteration
    dir_iteration = chk.mapping_iteration(uuid, prj_name, front_iteration, front=True)
    if "error" in dir_iteration:
        return error_msg(400, {}, str(dir_iteration[1]), log=True)
    # Get model.json
    if type == "object_detection":
        model = "yolo"
    elif type == "classification":
        model = type
    # Check convert model does not exist
    status = check_convert_exist(type, prj_name, dir_iteration, export_platform)
    ct_model = Convert_model(uuid, prj_name, dir_iteration, front_iteration, export_platform)
    if status:
        # Setting model.json
        set_export_json(model, prj_name, dir_iteration, export_platform)
        # Run command
        command = 'python3 adapter.py -c {} --convert'.format(ROOT + '/' +prj_name+'/'+ dir_iteration + '/'+ model + '.json')
        # Covert model
        ct_model.thread_convert(command)
        return success_msg(200, {}, "Success", "Start to convert the model to a/an [{}] model.".format(export_platform))
    else:
        error_db = ct_model.check_file()
        if error_db:
            return error_msg(400, {}, str(error_db[1]))
        return success_msg(200, {}, "Success", "The model has been converted:[Platform:{}, Project:{}/{}]".format(export_platform, prj_name, front_iteration))

@app_export.route('/<uuid>/stop_converting', methods=['GET']) 
@swag_from("{}/{}".format(YAML_PATH, "stop_converting.yml"))
def stop_converting(uuid):
    # Check uuid is/isnot in app.config["PROJECT_INFO"]
    if not ( uuid in app.config["PROJECT_INFO"].keys()):
        return error_msg(400, {}, "UUID:{} does not exist.".format(uuid), log=True)
    # Get project name
    prj_name = app.config["PROJECT_INFO"][uuid]["project_name"]
    # Check is running thread
    if len(EXPORT_LIST) > 0:
        # Port - Processing
        target, http_port = request.environ['HTTP_HOST'].split(":")
        server_port = request.environ['SERVER_PORT']
        if http_port == server_port:
            port = http_port
        elif http_port != server_port:
            port = http_port + "/ivit"
        # IP - Processing
        if target == "127.0.0.1" or target == "localhost":
            target = app.config["HOST"]
        http_ip = get_target_addr(target)
        host = http_ip + ":" + port
        return success_msg(200, {"url":"{}/{}/{}/share".format(host, uuid, front_iteration)}, "Success")
    else:
        return error_msg(400, {}, "Threading does not exist in iteration of the Project:[{}:{}]".format(prj_name, iter_name), log=True)

@app.route('/<uuid>/share_api', methods=['POST'])
@swag_from("{}/{}".format(YAML_PATH, "share_api.yml"))
def share_api(uuid):
    # Check uuid is/isnot in app.config["PROJECT_INFO"]
    if not ( uuid in app.config["PROJECT_INFO"].keys()):
        return error_msg(400, {}, "UUID:{} does not exist.".format(uuid), log=True)
    # Check key of front
    if not "iteration" in request.get_json().keys():
        return error_msg(400, {}, "KEY:iteration does not exist.", log=True)
    # Get project name
    prj_name = app.config["PROJECT_INFO"][uuid]["project_name"]
    # Get iteration folder name (Get value of front)
    front_iteration = request.get_json()['iteration']
    # Mapping iteration
    dir_iteration = chk.mapping_iteration(uuid, prj_name, front_iteration, front=True)
    if "error" in dir_iteration:
        return error_msg(400, {}, str(dir_iteration[1]), log=True)
    # Setting path
    zip_file = ROOT + '/' + prj_name + "/" + dir_iteration + "/" + prj_name + ".zip"
    if exists(zip_file):
        return success_msg(200, {"url":"{}:{}/{}/{}/share".format(app.config["HOST"], request.environ['SERVER_PORT'], uuid, front_iteration)}, "Success")
    else:
        return error_msg(400, {}, "This {}.zip does not exist in iteration of the Project:[{}:{}]".format(prj_name, prj_name, front_iteration), log=True)

@app.route('/<uuid>/<iteration>/share', methods=['GET'])
# @swag_from("{}/{}".format(YAML_PATH, "share.yml"))
def share(uuid, iteration):
    # Check uuid is/isnot in app.config["PROJECT_INFO"]
    if not ( uuid in app.config["PROJECT_INFO"].keys()):
        return error_msg(400, {}, "UUID:{} does not exist.".format(uuid))
    # Get project name
    prj_name = app.config["PROJECT_INFO"][uuid]["project_name"]
    # Export path
    path = str(Path(__file__).resolve().parents[1]/"")
    front_iteration = iteration
    # Mapping iteration
    dir_iteration = chk.mapping_iteration(uuid, prj_name, front_iteration, front=True)
    if "error" in dir_iteration:
        return error_msg(400, {}, str(dir_iteration[1]), log=True)
    main_path = path + "/project/" + prj_name + "/" + dir_iteration
    filename = prj_name + ".zip"
    # check zip exist
    zip_file = main_path + "/" +  filename
    if exists(zip_file):
        return send_from_directory(directory=main_path, path=filename, as_attachment=True)
    else:
        return error_msg(400, {}, "This {}.zip does not exist in iteration of the Project:[{}:{}]".format(prj_name, prj_name, front_iteration), log=True)

@app.route('/export_status', methods=['GET'])
@swag_from("{}/{}".format(YAML_PATH, "export_status.yml"))
def export_status():
    return success_msg(200, 
        {
            "URL":True,
            "local":True,
            "iCAP": app.config["ICAP_STATUS"]
        },
        "Success"
    )

@app.route('/<uuid>/export_icap', methods=['POST'])
@swag_from("{}/{}".format(YAML_PATH, "export_icap.yml"))
def export_icap(uuid):
    # Check uuid is/isnot in app.config["PROJECT_INFO"]
    if not ( uuid in app.config["PROJECT_INFO"].keys()):
        return error_msg(400, {}, "UUID:{} does not exist.".format(uuid), log=True)
    # Check key of front
    if not "iteration" in request.get_json().keys():
        return error_msg(400, {}, "KEY:iteration does not exist.", log=True)
    # Get type
    type = app.config["PROJECT_INFO"][uuid]["type"]
    # Get project name
    prj_name = app.config["PROJECT_INFO"][uuid]["project_name"]
    # Get iteration folder name (Get value of front)
    front_iteration = request.get_json()['iteration']
    # Mapping iteration
    dir_iteration = chk.mapping_iteration(uuid, prj_name, front_iteration, front=True)
    if "error" in dir_iteration:
        return error_msg(400, {}, str(dir_iteration[1]), log=True)
    # Export path
    export_path = ROOT + '/' + prj_name + "/" + dir_iteration + "/export"
    # Get model.json
    if type == "object_detection":
        model = "yolo"
    elif type == "classification":
        model = type
    config_path = export_path + "/" + model + ".json"
    if not exists(config_path):
        return error_msg(400, {}, "The config of export does not exist in the Project:[{}]".format(config_path), log=True)
    # Get export platform
    export_platform = read_json(config_path)["export_platform"]
    # Setting path
    zip_folder = export_path.split("export")[0]
    filename = prj_name + ".zip"
    if exists(zip_folder + filename):
        # Checksum
        res = icap_upload_file(zip_folder, filename, app.config["TB_DEVICE_ID"], prj_name, export_platform, app.config["TB"], app.config["TB_PORT"])
        if "5" in str(res.status_code) or "4" in str(res.status_code):
            logging.error("Upload files status:{}".format(res.status_code))
            return error_msg(400, {}, res.json()["error"], log=True)
        logging.info("Upload files status:{}".format(res.status_code))
        success_info = res.json()
        # Update thingsboard model info
        res = post_metadata(success_info, prj_name, export_platform, type, export_path, app.config["TB"], app.config["TB_PORT"])
        if "5" in str(res.status_code) or "4" in str(res.status_code):
            logging.error("The status of post metadata:{}".format(res.status_code))
            return error_msg(400, {}, res.json()["error"], log=True)
        return success_msg(200, res.json()["data"], "Success", "The status of post metadata:{}".format(res.status_code))
    else:
        return error_msg(400, {}, "This {}.zip does not exist in iteration of the Project:[{}:{}]".format(prj_name, prj_name, front_iteration), log=True)
