from flask import Blueprint, request, jsonify
from flasgger import swag_from
import logging, os, shutil, copy
from webapi import app
from .common.utils import exists, success_msg, error_msg, read_json, regular_expression, special_words
from .common.config import PLATFORM_CFG, ROOT, YAML_MAIN_PATH
from .common.init_tool import get_project_info, fill_in_prjdict
from .common.database import PJ_INFO_DB, fill_in_db, delete_data_table_cmd, execute_db, update_data_table_cmd
from .common.inspection import Check, create_pj_dir
chk = Check()
app_cl_pj = Blueprint( 'control_project', __name__)
# Define API Docs path and Blue Print
YAML_PATH       = YAML_MAIN_PATH + "/control_project"

@app_cl_pj.route('/init_project', methods=['GET']) 
@swag_from("{}/{}".format(YAML_PATH, "init_project.yml"))
def init_project():
    logging.info("Get all project information!")
    # Initial_new app.config['UUID_LIST']/app.config["PROJECT_INFO"]
    app.config['UUID_LIST']={}
    app.config["PROJECT_INFO"]={}
    # Get all project info
    info = get_project_info()
    if info is not None:
        return error_msg(str(info))
        
    logging.info("Project:{}".format(app.config['UUID_LIST']))
    return jsonify(app.config["PROJECT_INFO"])

@app_cl_pj.route('/get_all_project', methods=['GET']) 
@swag_from("{}/{}".format(YAML_PATH, "get_all_project.yml"))
def get_all_project():
    logging.info("Get information from app.config['PROJECT_INFO']!")
    return app.config["PROJECT_INFO"]

@app_cl_pj.route('/get_type', methods=['GET']) 
@swag_from("{}/{}".format(YAML_PATH, "get_type.yml"))
def get_type():
    type = {"type": list(app.config['MODEL']["other"].keys())}
    return jsonify(type)

@app_cl_pj.route('/get_platform', methods=['GET']) 
@swag_from("{}/{}".format(YAML_PATH, "get_platform.yml"))
def get_platform():
    config = read_json(PLATFORM_CFG)
    platform = {"platform":config["platform"]}
    return jsonify(platform)

@app_cl_pj.route('/create_project', methods=['POST']) 
@swag_from("{}/{}".format(YAML_PATH, "create_project.yml"))
def create_project():
    if request.method=='POST':
        pj_info_db = copy.deepcopy(PJ_INFO_DB)
        # Receive JSON and check param is/isnot None
        param = request.get_json()
        status, msg = chk.front_param_isnull(param)
        if not status:
            return error_msg("This keys:{} is not fill in.".format(msg))
        # Regular_expression
        for key in param:
            if key == "project_name" and special_words(param[key]):
                return error_msg("The project_name include special characters:[{}]".format(param[key]))
            else:
                param[key] = regular_expression(param[key])

        # Create project folder and create workspace in project folder
        error = create_pj_dir(param['project_name'])
        if error:
            return error_msg(error)
        # Fill in dict before db 
        sample_dict = {param['project_name']:param}
        pj_info, _ = fill_in_prjdict(param['project_name'], pj_info_db, {}, sample_dict)
        # Insert to db
        info = fill_in_db(pj_info, 0, "project")
        if info is not None:
            return error_msg(str(info))
        # Insert to cfg
        info = get_project_info()
        if info is not None:
            return error_msg(str(info))

        key = [k for k, v in app.config["UUID_LIST"].items() if v == param['project_name']][0]
        return success_msg("Create new project:[{}:{}]".format(key, param['project_name']))

@app_cl_pj.route('/<uuid>/delete_project', methods=['DELETE']) 
@swag_from("{}/{}".format(YAML_PATH, "delete_project.yml"))
def delete_project(uuid):
    # Check uuid is/isnot in app.config["PROJECT_INFO"]
    if not ( uuid in app.config["PROJECT_INFO"].keys()):
        return error_msg("UUID:{} does not exist.".format(uuid))
    # Get project name
    prj_name = app.config["UUID_LIST"][uuid]
    # Delete folder, app.config["PROJECT_INFO"], app.config["UUID_LIST"], database
    if os.path.isdir(ROOT + '/' +prj_name):
        # Delete data from folder
        shutil.rmtree(ROOT + '/' +prj_name)
        # Delete data from app.config
        del app.config["PROJECT_INFO"][uuid]
        del app.config["UUID_LIST"][uuid]
        # Delete data from Database
        command = delete_data_table_cmd("project", "project_uuid=\'{}\'".format(uuid))
        info_db = execute_db(command, True)
        if info_db is not None:
            return error_msg(str(info_db[1])) 

        return success_msg("Delete project:[{}:{}]".format(uuid, prj_name))
    else:
        return error_msg("This project does not exist!:[{}]".format(prj_name))

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
        prj_name = app.config["PROJECT_INFO"][uuid]["project_name"]
        # Get value of front
        new_name = request.get_json()['new_name']
        # Regular expression
        new_name = regular_expression(new_name)
        # Change app.config["PROJECT_INFO"][uuid][”project_name”] 
        app.config["PROJECT_INFO"][uuid]["project_name"] = new_name
        # Change app.config["UUID_LIST"]
        app.config["UUID_LIST"][uuid] = new_name
        # Change folder name
        if not exists(ROOT + '/' +prj_name):
            return error_msg("The project does not exist:[{}]".format(prj_name))
        os.rename(ROOT + '/' +prj_name, ROOT + '/' +new_name)
        # Change project name from database
        show_image_path = ""
        if exists("./project/{}/cover.jpg".format(new_name)):
            show_image_path = "/display_img/project/{}/cover.jpg".format(new_name)
        value = "project_name=\'{}\', show_image_path=\'{}\'".format(new_name, show_image_path)
        command = update_data_table_cmd("project", value, "project_uuid=\'{}\'".format(uuid))
        info_db = execute_db(command, True)
        if info_db is not None:
            return error_msg(str(info_db[1]))
        
        logging.info("Renamed project:{} from {}".format(new_name, prj_name))
        return jsonify(request.get_json())
