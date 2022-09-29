from flask import Blueprint, request, jsonify, send_from_directory
from flasgger import swag_from
from pathlib import Path
from webapi import app
from .common.utils import MAINCFGPAHT, exists,read_json, success_msg, error_msg, YAML_MAIN_PATH
from .common.training_tool import Fillin
from .common.export_tool import set_export_json, convert_model
from .common.inspection import Check
chk = Check()
ct_model = convert_model()
fill_in = Fillin()

app_export = Blueprint( 'export_model', __name__)
# Define API Docs path and Blue Print
YAML_PATH       = YAML_MAIN_PATH + "/export_model"

@app_export.route('/<uuid>/get_export_platform', methods=['GET']) 
@swag_from("{}/{}".format(YAML_PATH, "get_export_platform.yml"))
def get_export_platform(uuid):
    # Check uuid is/isnot in app.config["PROJECT_INFO"]
    if not ( uuid in app.config["PROJECT_INFO"].keys()):
        return error_msg("UUID:{} is not exist.".format(uuid))
    # Get platform
    platform = app.config["PROJECT_INFO"][uuid]["front_project"]["platform"]
    # Get all platform list
    platform_list = read_json(MAINCFGPAHT)["platform"]
    # Filter platform
    if "xilinx" == platform:
        return jsonify({"export_platform":[platform]})
    else:
        platform = [ val for val in platform_list if val != "xilinx"]
        return jsonify({"export_platform":platform})

@app_export.route('/<uuid>/start_convert', methods=['POST']) 
@swag_from("{}/{}".format(YAML_PATH, "start_convert.yml"))
def start_convert(uuid):
    if request.method == 'POST':
        # Check uuid is/isnot in app.config["PROJECT_INFO"]
        if not ( uuid in app.config["PROJECT_INFO"].keys()):
            return error_msg("UUID:{} is not exist.".format(uuid))
        # Check key of front
        if not "iteration" in request.get_json().keys():
            return error_msg("KEY:iteration is not exist.")
        if not "export_platform" in request.get_json().keys():
            return error_msg("KEY:export_platform is not exist.")
        # Get project name
        prj_name = app.config["PROJECT_INFO"][uuid]["front_project"]["project_name"]
        # Get type
        type = app.config["PROJECT_INFO"][uuid]["front_project"]["type"]
        # Get iteration folder name (Get value of front)
        iter_name = request.get_json()['iteration']
        # Get export_platform (Get value of front)
        export_platform = request.get_json()['export_platform']
        # Setting config.json
        fill_in.set_config_json(prj_name, iter_name, type)
        # Setting model.json and front_train.json
        set_export_json(type, prj_name, iter_name, export_platform)
        # Run command
        command = 'python3 convert.py'
        # Covert model
        ct_model.thread_convert(command, uuid, prj_name, iter_name, export_platform)

        return success_msg("Start to convert model to {}.".format(export_platform))

# @app.route('/<uuid>/download', methods=['POST'])
# @swag_from("{}/{}".format(YAML_PATH, "download.yml"))
# def download(uuid):
#     if request.method == 'POST':
#         # Check uuid is/isnot in app.config["PROJECT_INFO"]
#         if not ( uuid in app.config["PROJECT_INFO"].keys()):
#             return error_msg("UUID:{} is not exist.".format(uuid))
#         # Check key of front
#         if not "iteration" in request.get_json().keys():
#             return error_msg("KEY:iteration is not exist.")
#         # Get project name
#         prj_name = app.config["PROJECT_INFO"][uuid]["front_project"]["project_name"]
#         # Get iteration folder name (Get value of front)
#         iter_name = request.get_json()['iteration']
#         # Export path
#         path = str(Path(__file__).resolve().parents[1]/"")
#         export_path = path+"/Project/"+prj_name+"/"+iter_name+"/export"
#         # Setting path
#         zip_folder = export_path.split("export")[0]
#         filename = prj_name+".zip"
#         if exists(zip_folder+filename):
#             return send_from_directory(directory=export_path.split("export")[0], path=prj_name+".zip", as_attachment=True)
#         else:
#             return error_msg("This {}.zip is not exist.".format(prj_name))

@app.route('/<uuid>/share_api', methods=['POST'])
@swag_from("{}/{}".format(YAML_PATH, "share_api.yml"))
def share_api(uuid):
    if request.method == 'POST':
        # Check uuid is/isnot in app.config["PROJECT_INFO"]
        if not ( uuid in app.config["PROJECT_INFO"].keys()):
            return error_msg("UUID:{} is not exist.".format(uuid))
        # Check key of front
        if not "iteration" in request.get_json().keys():
            return error_msg("KEY:iteration is not exist.")
        # Get project name
        prj_name = app.config["PROJECT_INFO"][uuid]["front_project"]["project_name"]
        # Get iteration folder name (Get value of front)
        iter_name = request.get_json()['iteration']
        # Export path
        export_path = "./Project/"+prj_name+"/"+iter_name+"/export"
        # Setting path
        zip_folder = export_path.split("export")[0]
        filename = prj_name+".zip"
        if exists(zip_folder+filename):
            return success_msg("{}:{}/{}/{}/share".format(request.environ['SERVER_NAME'], request.environ['SERVER_PORT'], uuid, iter_name))
        else:
            return error_msg("This {}.zip is not exist.".format(prj_name))

@app.route('/<uuid>/<iteration>/share', methods=['GET'])
@swag_from("{}/{}".format(YAML_PATH, "share.yml"))
def share(uuid, iteration):
    # Check uuid is/isnot in app.config["PROJECT_INFO"]
    if not ( uuid in app.config["PROJECT_INFO"].keys()):
        return error_msg("UUID:{} is not exist.".format(uuid))
    # Get project name
    prj_name = app.config["PROJECT_INFO"][uuid]["front_project"]["project_name"]
    # Export path
    path = str(Path(__file__).resolve().parents[1]/"")
    export_path = path+"/Project/"+prj_name+"/"+iteration+"/export"
    # check zip exist
    zip_folder = export_path.split("export")[0]
    filename = prj_name+".zip"
    if exists(zip_folder+filename):
        return send_from_directory(directory=export_path.split("export")[0], path=prj_name+".zip", as_attachment=True)
    else:
        return error_msg("This {}.zip is not exist.".format(prj_name))