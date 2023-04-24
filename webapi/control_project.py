from flask import Blueprint, request, jsonify
from flasgger import swag_from
import logging, os, shutil, copy
from webapi import app
from .common.utils import exists, success_msg, error_msg, read_json, regular_expression, special_words
from .common.config import PLATFORM_CFG, ROOT, YAML_MAIN_PATH
from .common.init_tool import get_project_info, fill_in_prjdict
from .common.database import PJ_INFO_DB, fill_in_db, delete_data_table_cmd, update_data_table_cmd
from .common.inspection import Check, create_pj_dir, change_docs_prjname
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
    error_db = get_project_info()
    # Error
    if error_db:
        return error_msg(400, {}, str(error_db[1]))
    logging.info("Project:{}".format(app.config['UUID_LIST']))
    return success_msg(200, app.config["PROJECT_INFO"], "Success")

@app_cl_pj.route('/get_all_project', methods=['GET']) 
@swag_from("{}/{}".format(YAML_PATH, "get_all_project.yml"))
def get_all_project():
    logging.info("Get information from app.config['PROJECT_INFO']!")
    return success_msg(200, app.config["PROJECT_INFO"], "Success") 

@app_cl_pj.route('/get_type', methods=['GET']) 
@swag_from("{}/{}".format(YAML_PATH, "get_type.yml"))
def get_type():
    type = {"type": list(app.config['MODEL']["other"].keys())}
    return success_msg(200, type, "Success")

@app_cl_pj.route('/get_platform', methods=['GET']) 
@swag_from("{}/{}".format(YAML_PATH, "get_platform.yml"))
def get_platform():
    config = read_json(PLATFORM_CFG)
    platform = {"platform":config["platform"]}
    return success_msg(200, platform, "Success")

@app_cl_pj.route('/create_project', methods=['POST']) 
@swag_from("{}/{}".format(YAML_PATH, "create_project.yml"))
def create_project():
    pj_info_db = copy.deepcopy(PJ_INFO_DB)
    # Receive JSON and check param is/isnot None
    param = request.get_json()
    msg = chk.front_param_isnull(param)
    if msg:
        return error_msg(400, {}, "Keys:{} is not filled in.".format(msg), log=True)
    # Regular_expression
    for key in param:
        if key == "project_name" and special_words(param[key]):
            return error_msg(400, {}, "The project_name includes special characters:[{}]".format(param[key]), log=True)
        else:
            param[key] = regular_expression(param[key])
    # Create project folder and create workspace in project folder
    msg = create_pj_dir(param['project_name'])
    if msg:
        return error_msg(400, {}, str(msg), log=True)
    # Fill in dict before db 
    sample_dict = {param['project_name']:param}
    pj_info, _ = fill_in_prjdict(param['project_name'], pj_info_db, {}, sample_dict)
    # Insert to db
    error_db = fill_in_db(pj_info, 0, "project")
    if error_db:
        return error_msg(400, {}, str(error_db[1]))
    # Insert to cfg
    error_db = get_project_info()
    if error_db:
        return error_msg(400, {}, str(error_db[1]))
    # Success
    key = [k for k, v in app.config["UUID_LIST"].items() if v == param['project_name']][0]
    return success_msg(200, {}, "Success", "Create new project:[{}:{}]".format(key, param['project_name']))

@app_cl_pj.route('/<uuid>/delete_project', methods=['DELETE']) 
@swag_from("{}/{}".format(YAML_PATH, "delete_project.yml"))
def delete_project(uuid):
    # Check uuid is/isnot in app.config["PROJECT_INFO"]
    if not ( uuid in app.config["PROJECT_INFO"].keys()):
        return error_msg(400, {}, "UUID:{} does not exist.".format(uuid), log=True)
    # Get project name
    prj_name = app.config["UUID_LIST"][uuid]
    # Delete folder, app.config["PROJECT_INFO"], app.config["UUID_LIST"], database
    if os.path.isdir(ROOT + '/' + prj_name) and prj_name != "":
        # Delete data from folder
        shutil.rmtree(ROOT + '/' + prj_name)
        # Delete data from app.config
        del app.config["PROJECT_INFO"][uuid]
        del app.config["UUID_LIST"][uuid]
        # Delete data from Database
        error_db = delete_data_table_cmd("project", "project_uuid=\'{}\'".format(uuid))
        if error_db:
            return error_msg(400, {}, str(error_db[1])) 
        return success_msg(200, {}, "Success", "Deleted project:[{}:{}]".format(uuid, prj_name))
    else:
        return  error_msg(400, {}, "This project does not exist!:[{}]".format(prj_name), log=True)

@app_cl_pj.route('/<uuid>/rename_project', methods=['PUT']) 
@swag_from("{}/{}".format(YAML_PATH, "rename_project.yml"))
def rename_project(uuid):
    # Check uuid is/isnot in app.config["PROJECT_INFO"]
    if not ( uuid in app.config["PROJECT_INFO"].keys()):
        return error_msg("UUID:{} does not exist.".format(uuid))
    # Check key of front
    if not "new_name" in request.get_json().keys():
        return error_msg("KEY:new_name does not exist.")
    # Get project name
    prj_name = app.config["PROJECT_INFO"][uuid]["project_name"]
    # Get type
    type = app.config["PROJECT_INFO"][uuid]["type"]
    # Get value of front
    new_name = request.get_json()['new_name']
    if special_words(new_name) :
        return error_msg(400, {}, "The project_name include special characters:[{}]".format(new_name), log=True)
    # Regular expression
    new_name = regular_expression(new_name)
    # Change app.config["PROJECT_INFO"][uuid][”project_name”] 
    app.config["PROJECT_INFO"][uuid]["project_name"] = new_name
    # Change app.config["UUID_LIST"]
    app.config["UUID_LIST"][uuid] = new_name
    # Change folder name
    main_path = ROOT + '/' + prj_name
    new_main_path = ROOT + '/' + new_name
    if not exists(main_path):
        return error_msg(400, {}, "The project does not exist:[{}]".format(prj_name), log=True)
    os.rename(main_path, new_main_path)
    # Change project name from database
    show_image_path = ""
    if exists("./project/{}/cover.jpg".format(new_name)):
        show_image_path = "/display_img/project/{}/cover.jpg".format(new_name)
    value = "project_name=\'{}\', show_image_path=\'{}\'".format(new_name, show_image_path)
    error_db = update_data_table_cmd("project", value, "project_uuid=\'{}\'".format(uuid))
    if error_db:
        return error_msg(str(error_db[1]))
    # Change project name in all iteration documents
    iter_name = [ os.path.join(new_main_path, name) for name in os.listdir(new_main_path) if name != "workspace" and os.path.isdir(os.path.join(new_main_path, name))]
    if len(iter_name) > 0:
        change_docs_prjname(iter_name, prj_name, new_name, type)
    logging.info("Renamed project:{} from {}".format(new_name, prj_name))

    return success_msg(200, request.get_json(), "Success", "Renamed project:{} from {}".format(new_name, prj_name))
