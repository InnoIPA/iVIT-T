from flask import Blueprint, request, jsonify
from flasgger import swag_from
import logging
import os, shutil

from webapi import app
from .common.utils import success_msg, error_msg, write_json, read_json, MAINCFGPAHT, YAML_MAIN_PATH
from .common.init_tool import get_project_info, init_apps, cover_img, exist_iteration, count_effect_img
from .common.inspection import Check, create_pj_dir
chk = Check()

app_cl_pj = Blueprint( 'control_project', __name__)
app.config["PROJECT_INFO"]={}
app.config['NEW_PROJECT_CONFIG']={"front_project":
                                        {
                                            "project_name":None,
                                            "platform":None,
                                            "type":None,
                                        },      
                                }

app.config['MODEL']={ 
                    "other":{
                        "classification":['resnet_18','resnet_50'],
                        "object_detection": ['yolov4', 'yolov4-tiny']},
                    "xilinx":{            
                        "classification":['vgg_16','resnet_50'],
                        "object_detection": ['yolov4-leaky', 'yolov3-tiny']},
                }
# Define API Docs path and Blue Print
YAML_PATH       = YAML_MAIN_PATH + "/control_project"

@app_cl_pj.route('/init_project', methods=['GET']) 
@swag_from("{}/{}".format(YAML_PATH, "init_project.yml"))
def init_project():
    # Get all project info
    get_project_info()
    logging.info('Initial (project:{}) '.format(app.config["UUID_LIST"]))

    # Check PROJECT_INFO is null
    if not app.config["PROJECT_INFO"]:
        logging.warn("Any project does not exist in project folder.")
        return jsonify({})

    for uuid in app.config["PROJECT_INFO"]:
        logging.info("Get info of project:[uuid:{},prj_name:{}]".format(uuid, app.config["PROJECT_INFO"][uuid]["front_project"]["project_name"]))
        # Cover image sent to front
        cover_img(uuid)
        # Count iteration
        exist_iteration(uuid)
        # Count effect img
        count_effect_img(uuid)

    return app.config["PROJECT_INFO"]

@app_cl_pj.route('/get_all_project', methods=['GET']) 
@swag_from("{}/{}".format(YAML_PATH, "get_all_project.yml"))
def get_all_project():
    return app.config["PROJECT_INFO"]

@app_cl_pj.route('/get_type', methods=['GET']) 
@swag_from("{}/{}".format(YAML_PATH, "get_type.yml"))
def get_type():
    type = {"type": list(app.config['MODEL']["other"].keys())}
    return jsonify(type)

@app_cl_pj.route('/get_platform', methods=['GET']) 
@swag_from("{}/{}".format(YAML_PATH, "get_platform.yml"))
def get_platform():
    config = read_json(MAINCFGPAHT)
    platform = {"platform":config["platform"]}
    return jsonify(platform)

@app_cl_pj.route('/create_project', methods=['POST']) 
@swag_from("{}/{}".format(YAML_PATH, "create_project.yml"))
def create_project():
    if request.method=='POST':
        logging.info('Create Project.')
        # Receive JSON and check param is/isnot None
        param = request.get_json()
        status, msg = chk.front_param_isnull(param)
        if not status:
            return error_msg("This keys:{} is not fill in.".format(msg))
        
        # fill in app.config['NEW_PROJECT_CONFIG']["front_project"]
        for key in param.keys():
            app.config['NEW_PROJECT_CONFIG']["front_project"][key] = param[key]
            if key == "project_name":
                # Create project folder and create workspace in project folder
                create_pj_dir(app.config['NEW_PROJECT_CONFIG']["front_project"][key])

        # Create front_project.json in project folderf
        front_pj_param = './Project/'+app.config['NEW_PROJECT_CONFIG']["front_project"]["project_name"]+'/front_project.json'
        write_json(front_pj_param, app.config['NEW_PROJECT_CONFIG']["front_project"])

        # Build uuid
        init_apps(app.config['NEW_PROJECT_CONFIG']["front_project"]["project_name"])

        return success_msg("Create new project:{}".format(app.config['NEW_PROJECT_CONFIG']["front_project"]["project_name"]))

@app_cl_pj.route('/<uuid>/delete_project', methods=['DELETE']) 
@swag_from("{}/{}".format(YAML_PATH, "delete_project.yml"))
def delete_project(uuid):
    # Check uuid is/isnot in app.config["PROJECT_INFO"]
    if not ( uuid in app.config["PROJECT_INFO"].keys()):
        return error_msg("UUID:{} does not exist.".format(uuid))
    # Get project name
    prj_name = app.config["PROJECT_INFO"][uuid]["front_project"]["project_name"]

    # Delete dir and file and global variable
    if os.path.isdir("./Project/"+prj_name):
        shutil.rmtree("./Project/"+prj_name)
        del app.config["PROJECT_INFO"][uuid]
        del app.config["UUID_LIST"][prj_name]

        return success_msg("Delete project:{}!".format(prj_name))
    else:
        return error_msg("This {} folder does not exist!".format(prj_name))

@app_cl_pj.route('/<uuid>/rename_project', methods=['PUT']) 
@swag_from("{}/{}".format(YAML_PATH, "rename_project.yml"))
def rename_project(uuid):
    if request.method == 'PUT':
        # Check uuid is/isnot in app.config["PROJECT_INFO"]
        if not ( uuid in app.config["PROJECT_INFO"].keys()):
            return error_msg("UUID:{} does not exist.".format(uuid))
        # Check key of front
        if not "new_name" in request.get_json().keys():
            return error_msg("KEY:new_name does not exist.")
        # Get project name
        prj_name = app.config["PROJECT_INFO"][uuid]["front_project"]["project_name"]
        # Get value of front
        new_name = request.get_json()['new_name']

        # Change app.config["PROJECT_INFO"][uuid]["front_project"][”project_name”] 
        app.config["PROJECT_INFO"][uuid]["front_project"]["project_name"]=new_name
        # Change app.config["UUID_LIST"]
        app.config["UUID_LIST"][new_name] = app.config["UUID_LIST"][prj_name]
        del app.config["UUID_LIST"][prj_name]
        # Change json[”project_name”]
        json_path = "./Project/"+prj_name+"/front_project.json"
        json_data=read_json(json_path)
        json_data["project_name"]=new_name
        write_json(json_path, json_data)
        # Change folder name
        os.rename("./Project/"+prj_name, "./Project/"+new_name)

        return jsonify(request.get_json())
