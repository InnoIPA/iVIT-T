from flask import Blueprint, request, jsonify
from flasgger import swag_from
import logging, os, shutil, json
from webapi import app
from .common.utils import exists, read_json, success_msg, error_msg, regular_expression
from .common.model_tools import model_info_db, del_model_db
from .common.config import ROOT, YAML_MAIN_PATH
from .common.inspection import Check
chk = Check()
app_cl_model = Blueprint( 'control_model', __name__)
# Define API Docs path and Blue Print
YAML_PATH       = YAML_MAIN_PATH + "/control_model"

@app_cl_model.route('/<uuid>/get_iteration', methods=['GET']) 
@swag_from("{}/{}".format(YAML_PATH, "get_iteration.yml"))
def get_iteration(uuid):
    # Check uuid is/isnot in app.config["PROJECT_INFO"]
    if not ( uuid in app.config["PROJECT_INFO"].keys()):
        return error_msg("UUID:{} does not exist.".format(uuid))
    # Get project name
    prj_name = app.config["PROJECT_INFO"][uuid]["project_name"]
    prj_path = ROOT + "/" + prj_name
    chk.update_mapping_name(prj_path, uuid)
    folder_name = list(app.config["MAPPING_ITERATION"][uuid].values())
    logging.info("Get iteration list:[{}:{}]".format(prj_name, folder_name))
    return jsonify({"folder_name":folder_name}) 

@app_cl_model.route('/<uuid>/get_model_info', methods=['POST']) 
@swag_from("{}/{}".format(YAML_PATH, "get_model_info.yml"))
def get_model_info(uuid):
    if request.method == 'POST':
        # Check uuid is/isnot in app.config["PROJECT_INFO"]
        if not ( uuid in app.config["PROJECT_INFO"].keys()):
            return error_msg("UUID:{} does not exist.".format(uuid))
        # Check key of front
        if not "iteration" in request.get_json().keys():
            return error_msg("KEY:iteration does not exist.")
        # Get project name
        prj_name = app.config["PROJECT_INFO"][uuid]["project_name"]
        # Get value of front
        front_iteration = request.get_json()['iteration']
        # Mapping iteration
        dir_iteration = chk.mapping_iteration(uuid, prj_name, front_iteration, front=True)
        if "error" in dir_iteration:
            return error_msg(str(dir_iteration[1]))
        # Get model info from model database
        info_db = model_info_db(uuid, prj_name, dir_iteration)
        # Prevent error 
        if type(info_db) == tuple:
            return error_msg(str(info_db[1]))
        logging.info("Get infomation of model:[{}:{}]".format(prj_name, front_iteration))
        return jsonify(info_db)

@app_cl_model.route('/<uuid>/delete_iteration', methods=['DELETE'])
@swag_from("{}/{}".format(YAML_PATH, "delete_iteration.yml"))
def delete_iteration(uuid):
    if request.method == 'DELETE':
        # Check uuid is/isnot in app.config["PROJECT_INFO"]
        if not ( uuid in app.config["PROJECT_INFO"].keys()):
            return error_msg("UUID:{} does not exist.".format(uuid))
        # Check key of front
        if not "iteration" in request.get_json().keys():
            return error_msg("KEY:iter_name does not exist.")
        # Get project name
        prj_name = app.config["PROJECT_INFO"][uuid]["project_name"]
        # Get value of front
        front_iteration = request.get_json()['iteration']
        # Mapping iteration
        prj_path = ROOT + "/" + prj_name
        dir_iteration = chk.mapping_iteration(uuid, prj_name, front_iteration, front=True)
        if "error" in dir_iteration:
            return error_msg(str(dir_iteration[1]))
        iter_path = prj_path + "/" + dir_iteration
        if os.path.isdir(iter_path):
            # Delete iteration
            shutil.rmtree(iter_path)
            # Update app.config["MAPPING_ITERATION"]
            chk.update_mapping_name(prj_path, uuid)
            # Detele data from database
            info_db = del_model_db(uuid, dir_iteration)
            if info_db is not None:
                return error_msg(str(info_db[1]))
            return success_msg("Delete {} in Project:{}".format(front_iteration, prj_name))
        else:
            return error_msg("This {} does not exist in Project:{}".format(front_iteration, prj_name))

@app_cl_model.route('/<uuid>/curve_history', methods=['POST']) 
@swag_from("{}/{}".format(YAML_PATH, "curve_history.yml"))
def curve_history(uuid):
    if request.method == 'POST':
        # Check uuid is/isnot in app.config["PROJECT_INFO"]
        if not ( uuid in app.config["PROJECT_INFO"].keys()):
            return error_msg("UUID:{} does not exist.".format(uuid))
        # Check key of front
        if not "iteration" in request.get_json().keys():
            return error_msg("KEY:iteration does not exist.")
        # Get project name
        prj_name = app.config["PROJECT_INFO"][uuid]["project_name"]
        # Get value of front
        front_iteration = request.get_json()['iteration']
        # Mapping iteration
        prj_path = ROOT + "/" + prj_name
        dir_iteration = chk.mapping_iteration(uuid, prj_name, front_iteration, front=True)
        if "error" in dir_iteration:
            return error_msg(str(dir_iteration[1]))
        iter_path = prj_path + "/" + dir_iteration
        # Get log
        graph_path = iter_path + "/weights/graph.txt"
        if os.path.isdir(iter_path):
            if exists(graph_path):
                graph = {} 
                with open(graph_path) as file:
                    for key,line in enumerate(file): 
                        json_acceptable_string = line.replace("'", "\"")
                        line = json.loads(json_acceptable_string)
                        graph.update({str(key+1):dict(line)})
                logging.info("Get curve history of Project:[{}:{}]".format(prj_name, front_iteration))
                return jsonify(graph)
            else:
                return error_msg("This graph.txt does not exist in [{}] of Project:[{}]".format(front_iteration, prj_name))
        else:
            return error_msg("This [{}] does not exist in Project:[{}]".format(front_iteration, prj_name))
        
@app_cl_model.route('/<uuid>/metrics_history', methods=['POST']) 
@swag_from("{}/{}".format(YAML_PATH, "metrics_history.yml"))
def metrics_history(uuid):
    if request.method == 'POST':
        # Check uuid is/isnot in app.config["PROJECT_INFO"]
        if not ( uuid in app.config["PROJECT_INFO"].keys()):
            return error_msg("UUID:{} does not exist.".format(uuid))
        # Check key of front
        if not "iteration" in request.get_json().keys():
            return error_msg("KEY:iteration does not exist.")
        # Get project name
        prj_name = app.config["PROJECT_INFO"][uuid]["project_name"]
        # Get value of front
        front_iteration = request.get_json()['iteration']
        # Mapping iteration
        prj_path = ROOT + "/" + prj_name
        dir_iteration = chk.mapping_iteration(uuid, prj_name, front_iteration, front=True)
        if "error" in dir_iteration:
            return error_msg(str(dir_iteration[1]))
        iter_path = prj_path + "/" + dir_iteration
        metrics_path = iter_path + "/weights/metrics.json"
        if os.path.isdir(iter_path):
            if exists(metrics_path):
                metrics = read_json(metrics_path)
                logging.info("Get metrics history of Project:[{}:{}]".format(prj_name, front_iteration))
                return jsonify(metrics)
            else:
                return error_msg("This metrics.json does not exist in [{}] of Project:[{}]".format(front_iteration, prj_name))
        else:
            return error_msg("This [{}] does not exist in Project:[{}]".format(front_iteration, prj_name))

@app_cl_model.route('/<uuid>/get_model_json', methods=['POST']) 
@swag_from("{}/{}".format(YAML_PATH, "get_model_json.yml"))
def get_model_json(uuid):
    if request.method == 'POST':
        # Check uuid is/isnot in app.config["PROJECT_INFO"]
        if not ( uuid in app.config["PROJECT_INFO"].keys()):
            return error_msg("UUID:{} does not exist.".format(uuid))
        # Check key of front
        if not "iteration" in request.get_json().keys():
            return error_msg("KEY:iteration does not exist.")
        # Get project name
        prj_name = app.config["PROJECT_INFO"][uuid]["project_name"]
        # Get type
        type = app.config["PROJECT_INFO"][uuid]["type"]
        # Get value of front
        front_iteration = request.get_json()['iteration']
        # Mapping iteration
        prj_path = ROOT + "/" + prj_name
        dir_iteration = chk.mapping_iteration(uuid, prj_name, front_iteration, front=True)
        if "error" in dir_iteration:
            return error_msg(str(dir_iteration[1]))
        iter_path = prj_path + "/" + dir_iteration
        if type == "object_detection":
            model = "yolo"
        else:
            model = "classification"
        train_param_path = iter_path+"/"+model+".json"
        model_param = {}
        if os.path.isdir(iter_path):
            # model.json
            if exists(train_param_path):
                train_param = read_json(train_param_path)
                model_param.update({"train_param":train_param})
            else:
                return error_msg("This model.json does not exist in [{}] of Project:[{}]".format(front_iteration, prj_name))
            return jsonify(model_param)
        else:
            return error_msg("This [{}] does not exist in Project:[{}]".format(front_iteration, prj_name))

@app_cl_model.route('/<uuid>/check_best_model', methods=['POST']) 
@swag_from("{}/{}".format(YAML_PATH, "check_best_model.yml"))
def check_best_model(uuid):
    if request.method == 'POST':
        # Check uuid is/isnot in app.config["PROJECT_INFO"]
        if not ( uuid in app.config["PROJECT_INFO"].keys()):
            return error_msg("UUID:{} does not exist.".format(uuid))
        # Check key of front
        if not "iteration" in request.get_json().keys():
            return error_msg("KEY:iteration does not exist.")
        # Get project name
        prj_name = app.config["PROJECT_INFO"][uuid]["project_name"]
        # Get type
        type = app.config["PROJECT_INFO"][uuid]["type"]
        # Get value of front
        front_iteration = request.get_json()['iteration']
        # Mapping iteration
        prj_path = ROOT + "/" + prj_name
        dir_iteration = chk.mapping_iteration(uuid, prj_name, front_iteration, front=True)
        if "error" in dir_iteration:
            return error_msg(str(dir_iteration[1]))
        iter_path = prj_path + "/" + dir_iteration
        if type == "object_detection":
            model = "yolo"
        else:
            model = "classification"
        train_param_path = iter_path + "/" + model + ".json"
        if os.path.isdir(iter_path):
            # model.json
            if exists(train_param_path):
                train_param = read_json(train_param_path)
                # Find best model path
                model_path = train_param["train_config"]["save_model_path"]
                best_list = [model for model in os.listdir(model_path) if "best" in model]
                if len(best_list) == 0:
                    return error_msg("This best model does not exist in [{}] of Project:[{}]".format(front_iteration, prj_name))
                else:
                    logging.info("This bast model dose exist.")
                    return success_msg("Exist.")
            else:
                return error_msg("This model.json does not exist in [{}] of Project:[{}]".format(front_iteration, prj_name))
        else:
            return error_msg("This {} does not exist in Project:{}".format(front_iteration, prj_name))