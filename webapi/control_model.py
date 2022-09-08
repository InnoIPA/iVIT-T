from flask import Blueprint, request, jsonify
from flasgger import swag_from
import logging
import os, shutil, json
from natsort import natsorted
from webapi import app
from .common.utils import exists, read_json, success_msg, error_msg

app_cl_model = Blueprint( 'control_model', __name__)

@app_cl_model.route('/<uuid>/get_iteration', methods=['GET']) 
@swag_from('./descript/control_model/get_iteration.yml')
def get_iteration(uuid):
    # Check uuid is/isnot in app.config["PROJECT_INFO"]
    if not ( uuid in app.config["PROJECT_INFO"].keys()):
        return error_msg("UUID:{} is not exist.".format(uuid))
    # Get project name
    prj_name = app.config["PROJECT_INFO"][uuid]["front_project"]["project_name"]
    prj_path = "./Project/"+prj_name
    folder_name = [ dir for dir in natsorted(os.listdir(prj_path)) if os.path.isdir(prj_path+"/"+dir) and dir != "workspace"]
    return jsonify({"folder_name":folder_name}) 

@app_cl_model.route('/<uuid>/get_model_info', methods=['POST']) 
@swag_from('./descript/control_model/get_model_info.yml')
def get_model_info(uuid):
    if request.method == 'POST':
        # Check uuid is/isnot in app.config["PROJECT_INFO"]
        if not ( uuid in app.config["PROJECT_INFO"].keys()):
            return error_msg("UUID:{} is not exist.".format(uuid))
        # Check key of front
        if not "iteration" in request.get_json().keys():
            return error_msg("KEY:iteration is not exist.")
        # Get project name
        prj_name = app.config["PROJECT_INFO"][uuid]["front_project"]["project_name"]
        # Get value of front
        iteration = request.get_json()['iteration']

        iter_path = "./Project/"+prj_name+"/"+iteration
        front_train_path = iter_path+"/front_train.json"
        if os.path.isdir(iter_path):
            if exists(front_train_path):
                train_info = read_json(front_train_path)
                # Remove export
                if "export_platform" in train_info:
                    del train_info['export_platform']

                return jsonify(train_info)
            else:
                return error_msg("This front_train.json is not exist in {} of Project:{}".format(iteration, prj_name))
        else:
            return error_msg("This {} is not exist in Project:{}".format(iteration, prj_name))

@app_cl_model.route('/<uuid>/delete_iteration', methods=['POST']) 
@swag_from('./descript/control_model/delete_iteration.yml')
def delete_iteration(uuid):
    if request.method == 'POST':
        # Check uuid is/isnot in app.config["PROJECT_INFO"]
        if not ( uuid in app.config["PROJECT_INFO"].keys()):
            return error_msg("UUID:{} is not exist.".format(uuid))
        # Check key of front
        if not "iteration" in request.get_json().keys():
            return error_msg("KEY:iter_name is not exist.")
        # Get project name
        prj_name = app.config["PROJECT_INFO"][uuid]["front_project"]["project_name"]
        # Get value of front
        iteration = request.get_json()['iteration']

        prj_path = "./Project/"+prj_name
        iter_path = prj_path+"/"+iteration
        if os.path.isdir(iter_path):
            # Delete all iteration
            shutil.rmtree(iter_path)
            # Check iteration name
            folder_name = [ dir for dir in natsorted(os.listdir(prj_path)) if os.path.isdir(prj_path+"/"+dir) and dir != "workspace"]
            # Rename folder and sort
            for num, name in enumerate(folder_name):
                os.rename(prj_path+"/"+name, prj_path+"/iteration"+str(num+1))

            logging.info("Renamed iteration1~iterationN in Project:{}".format(prj_name))
            return success_msg("Delete {} in Project:{}".format(iteration, prj_name))
        else:
            return error_msg("This {} is not exist in Project:{}".format(iteration, prj_name))

@app_cl_model.route('/<uuid>/curve_history', methods=['POST']) 
@swag_from('./descript/control_model/curve_history.yml')
def curve_history(uuid):
    if request.method == 'POST':
        # Check uuid is/isnot in app.config["PROJECT_INFO"]
        if not ( uuid in app.config["PROJECT_INFO"].keys()):
            return error_msg("UUID:{} is not exist.".format(uuid))
        # Check key of front
        if not "iteration" in request.get_json().keys():
            return error_msg("KEY:iteration is not exist.")
        # Get project name
        prj_name = app.config["PROJECT_INFO"][uuid]["front_project"]["project_name"]
        # Get value of front
        iteration = request.get_json()['iteration']

        iter_path = "./Project/"+prj_name+"/"+iteration
        front_train_path = iter_path+"/weights/graph.txt"
        if os.path.isdir(iter_path):
            if exists(front_train_path):
                graph = {} 
                with open(front_train_path) as file:
                    for key,line in enumerate(file): 
                        json_acceptable_string = line.replace("'", "\"")
                        line = json.loads(json_acceptable_string)
                        graph.update({str(key+1):dict(line)})
                return jsonify(graph)
            else:
                return error_msg("This graph.txt is not exist in {} of Project:{}".format(iteration, prj_name))
        else:
            return error_msg("This {} is not exist in Project:{}".format(iteration, prj_name))
        
@app_cl_model.route('/<uuid>/metrics_history', methods=['POST']) 
@swag_from('./descript/control_model/metrics_history.yml')
def metrics_history(uuid):
    if request.method == 'POST':
        # Check uuid is/isnot in app.config["PROJECT_INFO"]
        if not ( uuid in app.config["PROJECT_INFO"].keys()):
            return error_msg("UUID:{} is not exist.".format(uuid))
        # Check key of front
        if not "iteration" in request.get_json().keys():
            return error_msg("KEY:iteration is not exist.")
        # Get project name
        prj_name = app.config["PROJECT_INFO"][uuid]["front_project"]["project_name"]
        # Get value of front
        iteration = request.get_json()['iteration']

        iter_path = "./Project/"+prj_name+"/"+iteration
        metrics_path = iter_path+"/weights/metrics.json"
        if os.path.isdir(iter_path):
            if exists(metrics_path):
                metrics = read_json(metrics_path)
                return jsonify(metrics)
            else:
                return error_msg("This metrics.json is not exist in {} of Project:{}".format(iteration, prj_name))
        else:
            return error_msg("This {} is not exist in Project:{}".format(iteration, prj_name))

@app_cl_model.route('/<uuid>/get_model_json', methods=['POST']) 
@swag_from('./descript/control_model/get_model_json.yml')
def get_model_json(uuid):
    if request.method == 'POST':
        # Check uuid is/isnot in app.config["PROJECT_INFO"]
        if not ( uuid in app.config["PROJECT_INFO"].keys()):
            return error_msg("UUID:{} is not exist.".format(uuid))
        # Check key of front
        if not "iteration" in request.get_json().keys():
            return error_msg("KEY:iteration is not exist.")
        # Get project name
        prj_name = app.config["PROJECT_INFO"][uuid]["front_project"]["project_name"]
        # Get type
        type = app.config["PROJECT_INFO"][uuid]["front_project"]["type"]
        # Get value of front
        iteration = request.get_json()['iteration']

        iter_path = "./Project/"+prj_name+"/"+iteration
        front_train_path = iter_path+"/front_train.json"

        if type == "object_detection":
            model = "yolo"
        else:
            model = "classification"

        train_param_path = iter_path+"/"+model+".json"
        model_param = {}
        if os.path.isdir(iter_path):
            # front_train.json
            if exists(front_train_path):
                front_train = read_json(front_train_path)
                model_param.update({"front_train":front_train})
            else:
                return error_msg("This front_train.json is not exist in {} of Project:{}".format(iteration, prj_name))
            
            # model.json
            if exists(train_param_path):
                train_param = read_json(train_param_path)
                model_param.update({"train_param":train_param})
            else:
                return error_msg("This model.json is not exist in {} of Project:{}".format(type, iteration, prj_name))
                
            return jsonify(model_param)
        else:
            return error_msg("This {} is not exist in Project:{}".format(iteration, prj_name))

@app_cl_model.route('/<uuid>/check_best_model', methods=['POST']) 
@swag_from('./descript/control_model/check_best_model.yml')
def check_best_model(uuid):
    if request.method == 'POST':
        # Check uuid is/isnot in app.config["PROJECT_INFO"]
        if not ( uuid in app.config["PROJECT_INFO"].keys()):
            return error_msg("UUID:{} is not exist.".format(uuid))
        # Check key of front
        if not "iteration" in request.get_json().keys():
            return error_msg("KEY:iteration is not exist.")
        # Get project name
        prj_name = app.config["PROJECT_INFO"][uuid]["front_project"]["project_name"]
        # Get type
        type = app.config["PROJECT_INFO"][uuid]["front_project"]["type"]
        # Get value of front
        iteration = request.get_json()['iteration']

        if type == "object_detection":
            model = "yolo"
        else:
            model = "classification"

        iter_path = "./Project/"+prj_name+"/"+iteration
        train_param_path = iter_path+"/"+model+".json"

        if os.path.isdir(iter_path):
            # model.json
            if exists(train_param_path):
                train_param = read_json(train_param_path)
                # Find best model path
                model_path = train_param["train_config"]["save_model_path"]
                best_list = [model for model in os.listdir(model_path) if "best" in model]
                if len(best_list) == 0:
                    return error_msg("This best model is not exist in {} of Project:{}".format(type, iteration, prj_name))
                else:
                    return success_msg("Exist.")
            else:
                return error_msg("This model.json is not exist in {} of Project:{}".format(type, iteration, prj_name))
        else:
            return error_msg("This {} is not exist in Project:{}".format(iteration, prj_name))