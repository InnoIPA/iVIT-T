import os, logging
from flask import Blueprint, request, jsonify, send_from_directory
from flasgger import swag_from
from pathlib import Path
from webapi import app
from .common.utils import exists,read_json, success_msg, error_msg 
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
        return error_msg("UUID:{} does not exist.".format(uuid))
    if not arch:
        return error_msg("Arch is null.")
    # Get platform
    platform = app.config["PROJECT_INFO"][uuid]["platform"]
    # Get all platform list
    platform_list = read_json(PLATFORM_CFG)["platform"]
    # Filter platform
    type = app.config["PROJECT_INFO"][uuid]["type"]
    if "classification" == type:
        if "xilinx" == platform:
            return jsonify({"export_platform":platform_list})
        else:
            platform = [ val for val in platform_list if val != "xilinx"]
            return jsonify({"export_platform":platform})
        
    elif "object_detection" == type:
        if platform != "xilinx":
            if arch == "yolov4":
                platform = [ val for val in platform_list if val != "xilinx" and val != "hailo"]
                return jsonify({"export_platform":platform})
            if arch == "yolov4-tiny":
                platform = [ val for val in platform_list if val != "xilinx"]
                return jsonify({"export_platform":platform})
        else:
            return jsonify({"export_platform":platform_list})

@app_export.route('/<uuid>/start_converting', methods=['POST']) 
@swag_from("{}/{}".format(YAML_PATH, "start_converting.yml"))
def start_converting(uuid):
    if request.method == 'POST':
        # Check uuid is/isnot in app.config["PROJECT_INFO"]
        if not ( uuid in app.config["PROJECT_INFO"].keys()):
            return error_msg("UUID:{} does not exist.".format(uuid))
        # Check key of front
        if not "iteration" in request.get_json().keys():
            return error_msg("KEY:iteration does not exist.")
        if not "export_platform" in request.get_json().keys():
            return error_msg("KEY:export_platform does not exist.")
        # Get project name
        prj_name = app.config["PROJECT_INFO"][uuid]["project_name"]
        # Get type
        type = app.config["PROJECT_INFO"][uuid]["type"]
        # Get model.json
        if type == "object_detection":
            model = "yolo"
        elif type == "classification":
            model = type
        # Get export_platform (Get value of front)
        export_platform = request.get_json()['export_platform']
        front_iteration = request.get_json()['iteration']
        # Mapping iteration
        dir_iteration = chk.mapping_iteration(uuid, prj_name, front_iteration, front=True)
        if "error" in dir_iteration:
            return error_msg(str(dir_iteration[1]))
        # Check convert model does not exist
        status = check_convert_exist(type, prj_name, dir_iteration, export_platform)
        ct_model = Convert_model(uuid, prj_name, dir_iteration, front_iteration, export_platform)
        if status:
            # Setting model.json
            set_export_json(model, prj_name, dir_iteration, export_platform)
            # Run command
            command = 'python3 convert.py -c {}'.format(ROOT + '/' +prj_name+'/'+ dir_iteration + '/'+ model + '.json')
            # Covert model
            ct_model.thread_convert(command)
            return success_msg("Start to convert model to {}.".format(export_platform))
        else:
            info_db = ct_model.check_file()
            if info_db is not None:
                return error_msg(str(info_db[1]))
            return success_msg("The model has been converted:[Platform:{}, Project:{}/{}]".format(export_platform, prj_name, front_iteration))

@app_export.route('/<uuid>/stop_converting', methods=['GET']) 
@swag_from("{}/{}".format(YAML_PATH, "stop_converting.yml"))
def stop_converting(uuid):
    # Check uuid is/isnot in app.config["PROJECT_INFO"]
    if not ( uuid in app.config["PROJECT_INFO"].keys()):
        return error_msg("UUID:{} does not exist.".format(uuid))
    # Get project name
    prj_name = app.config["PROJECT_INFO"][uuid]["project_name"]
    # Check is running thread
    if len(EXPORT_LIST) > 0:
        # Get iteration name
        iter_name = EXPORT_LIST[0][uuid]["iteration"]
        # Stop converting
        EXPORT_LIST[0][uuid]['stop'].set()
        os.kill(int(EXPORT_LIST[0][uuid]['PID']), SIGKILL)
        return success_msg("Stop converting in iteration:[{}] of Project:[{}]".format(iter_name, prj_name))
    else:
        return error_msg("Thread does not exist in iteration of Project:[{}]".format(prj_name))

@app.route('/<uuid>/share_api', methods=['POST'])
@swag_from("{}/{}".format(YAML_PATH, "share_api.yml"))
def share_api(uuid):
    if request.method == 'POST':
        # Check uuid is/isnot in app.config["PROJECT_INFO"]
        if not ( uuid in app.config["PROJECT_INFO"].keys()):
            return error_msg("UUID:{} does not exist.".format(uuid))
        # Check key of front
        if not "iteration" in request.get_json().keys():
            return error_msg("KEY:iteration does not exist.")
        # Get project name
        prj_name = app.config["PROJECT_INFO"][uuid]["project_name"]
        # Get iteration folder name (Get value of front)
        front_iteration = request.get_json()['iteration']
        # Mapping iteration
        dir_iteration = chk.mapping_iteration(uuid, prj_name, front_iteration, front=True)
        if "error" in dir_iteration:
            return error_msg(str(dir_iteration[1]))
        # Export path
        export_path = ROOT + '/' + prj_name + "/" + dir_iteration + "/export"
        # Setting path
        zip_folder = export_path.split("export")[0]
        filename = prj_name+".zip"
        if exists(zip_folder+filename):
            return success_msg("{}:{}/{}/{}/share".format(request.environ['SERVER_NAME'], request.environ['SERVER_PORT'], uuid, front_iteration))
        else:
            return error_msg("This {}.zip does not exist.".format(prj_name))

@app.route('/<uuid>/<iteration>/share', methods=['GET'])
# @swag_from("{}/{}".format(YAML_PATH, "share.yml"))
def share(uuid, iteration):
    # Check uuid is/isnot in app.config["PROJECT_INFO"]
    if not ( uuid in app.config["PROJECT_INFO"].keys()):
        return error_msg("UUID:{} does not exist.".format(uuid))
    # Get project name
    prj_name = app.config["PROJECT_INFO"][uuid]["project_name"]
    # Export path
    path = str(Path(__file__).resolve().parents[1]/"")
    # Mapping iteration
    front_iteration = iteration
    dir_iteration = chk.mapping_iteration(uuid, prj_name, front_iteration, front=True)
    if "error" in dir_iteration:
        return error_msg(str(dir_iteration[1]))
    export_path = path + "/project/" + prj_name + "/" + dir_iteration + "/export"
    # check zip exist
    zip_folder = export_path.split("export")[0]
    filename = prj_name+".zip"
    if exists(zip_folder+filename):
        return send_from_directory(directory=export_path.split("export")[0], path=prj_name+".zip", as_attachment=True)
    else:
        return error_msg("This {}.zip does not exist.".format(prj_name))

@app.route('/export_status', methods=['GET'])
@swag_from("{}/{}".format(YAML_PATH, "export_status.yml"))
def export_status():
    return jsonify(
        {
            "URL":True,
            "local":True,
            "iCAP": app.config["ICAP_STATUS"]
        }
    )

@app.route('/<uuid>/export_icap', methods=['POST'])
@swag_from("{}/{}".format(YAML_PATH, "export_icap.yml"))
def export_icap(uuid):
    if request.method == 'POST':
        # Check uuid is/isnot in app.config["PROJECT_INFO"]
        if not ( uuid in app.config["PROJECT_INFO"].keys()):
            return error_msg("UUID:{} does not exist.".format(uuid))
        # Check key of front
        if not "iteration" in request.get_json().keys():
            return error_msg("KEY:iteration does not exist.")
        # Get platform
        platform = app.config["PROJECT_INFO"][uuid]["platform"]
        # Get type
        type = app.config["PROJECT_INFO"][uuid]["type"]
        # Get project name
        prj_name = app.config["PROJECT_INFO"][uuid]["project_name"]
        # Get iteration folder name (Get value of front)
        front_iteration = request.get_json()['iteration']
        
        # Mapping iteration
        dir_iteration = chk.mapping_iteration(uuid, prj_name, front_iteration, front=True)
        if "error" in dir_iteration:
            return error_msg(str(dir_iteration[1]))
        # Export path
        export_path = ROOT + '/' + prj_name + "/" + dir_iteration + "/export"
        # Setting path
        zip_folder = export_path.split("export")[0]
        filename = prj_name+".zip"
        if exists(zip_folder + filename):
            # Checksum
            res = icap_upload_file(zip_folder, filename, app.config["TB_DEVICE_ID"], prj_name, platform, app.config["TB"], app.config["TB_PORT"])
            if "5" in str(res.status_code) or "4" in str(res.status_code):
                logging.error("Upload files status:{}".format(res.status_code))
                return error_msg(res.json()["error"])
            logging.info("Upload files status:{}".format(res.status_code))
            success_info = res.json()
            # Update thingsboard model info
            res = post_metadata(success_info, prj_name, platform, type, export_path, app.config["TB"], app.config["TB_PORT"])
            if "5" in str(res.status_code) or "4" in str(res.status_code):
                logging.error("The status of post metadata:{}".format(res.status_code))
                return error_msg(res.json()["error"])
            logging.info("The status of post metadata:{}".format(res.status_code))
            return jsonify(res.json()), 200
        else:
            return error_msg("This {}.zip does not exist.".format(prj_name))
