from flask import Blueprint, request
from flasgger import swag_from
import os, shutil, json
from webapi import app
from .common.utils import exists, read_json, success_msg, error_msg
from .common.model_tool import model_info_db, del_model_db
from .common.config import ROOT, YAML_MAIN_PATH
from .common.inspection import Check
chk = Check()
app_cl_model = Blueprint( 'control_model', __name__)
# Define API Docs path and Blue Print
YAML_PATH       = YAML_MAIN_PATH + "/control_model"

@app_cl_model.route('/<uuid>/autolabel_get_iteration', methods=['GET']) 
@swag_from("{}/{}".format(YAML_PATH, "autolabel_get_iteration.yml"))
def autolabel_get_iteration(uuid):
    # Check uuid is/isnot in app.config["PROJECT_INFO"]
    if not ( uuid in app.config["PROJECT_INFO"].keys()):
        return error_msg(400, {}, "UUID:{} does not exist.".format(uuid), log=True)
    # Get project name
    prj_name = app.config["PROJECT_INFO"][uuid]["project_name"]
    type= app.config["PROJECT_INFO"][uuid]["type"]
    prj_path = ROOT + "/" + prj_name
    chk.update_mapping_name(prj_path, uuid)
    folder_name = list(app.config["MAPPING_ITERATION"][uuid].keys())
        
    _temp_folder_name=[]
    #get mAP and class info
    if type=="object_detection":

        for iter in folder_name:
            
            if app.config["SCHEDULE"].get_status(uuid,iter):
                continue
            _mAP=0
            _class_num=0
            #get mAP
            iter_path = ROOT + "/" + prj_name + "/" +iter
            if os.path.isdir(iter_path):
                metrics_path = iter_path + "/weights/metrics.json"
                if exists(metrics_path):
                    metrics = read_json(metrics_path)
                    _mAP = metrics["mAP"]
         
                else:
                    continue
            
            else:
                return error_msg(400, {}, "This iteration does not exist in the Project:[{}:{}]".format(prj_name, iter))

            #get class_num
            class_path = ROOT + "/" + prj_name + "/" +iter+"/dataset/classes.txt"
            with open(class_path,'r') as fp:
                all_lines = fp.readlines()
                _class_num = len(all_lines)
            _temp_json_info={}
            front_iter=app.config["MAPPING_ITERATION"][uuid][iter]
            _temp_json_info.update({front_iter:{"mAP":_mAP,"class":_class_num}})
            _temp_folder_name.append(_temp_json_info)
  
        return success_msg(200, {"folder_name":_temp_folder_name}, "Success", "Get iteration list:[{}:{}]".format(prj_name, _temp_folder_name))
    
    return success_msg(200, {"folder_name":folder_name}, "Success", "Get iteration list:[{}:{}]".format(prj_name, folder_name))


@app_cl_model.route('/<uuid>/get_iteration', methods=['GET']) 
@swag_from("{}/{}".format(YAML_PATH, "get_iteration.yml"))
def get_iteration(uuid):
    # Check uuid is/isnot in app.config["PROJECT_INFO"]
    if not ( uuid in app.config["PROJECT_INFO"].keys()):
        return error_msg(400, {}, "UUID:{} does not exist.".format(uuid), log=True)
    # Get project name
    prj_name = app.config["PROJECT_INFO"][uuid]["project_name"]
    type= app.config["PROJECT_INFO"][uuid]["type"]
    prj_path = ROOT + "/" + prj_name
    chk.update_mapping_name(prj_path, uuid)
    folder_name = list(app.config["MAPPING_ITERATION"][uuid].keys())
        
    _temp_folder_name=[]
    #get mAP and class info
    if type=="object_detection":

        for iter in folder_name:
            _mAP=0
            _class_num=0
            #get mAP
            iter_path = ROOT + "/" + prj_name + "/" +iter
            if os.path.isdir(iter_path):
                metrics_path = iter_path + "/weights/metrics.json"
                if exists(metrics_path):
                    metrics = read_json(metrics_path)
                    _mAP = metrics["mAP"]
         
                else:
                    return error_msg(400, {}, "This metrics.json does not exist in iteration of the Project:[{}:{}]".format(prj_name, iter))
            
            else:
                return error_msg(400, {}, "This iteration does not exist in the Project:[{}:{}]".format(prj_name, iter))

            #get class_num
            class_path = ROOT + "/" + prj_name + "/" +iter+"/dataset/classes.txt"
            with open(class_path,'r') as fp:
                all_lines = fp.readlines()
                _class_num = len(all_lines)
            _temp_json_info={}
            front_iter=app.config["MAPPING_ITERATION"][uuid][iter]
            _temp_json_info.update({front_iter:{"mAP":_mAP,"class":_class_num}})
            _temp_folder_name.append(_temp_json_info)
  
        return success_msg(200, {"folder_name":_temp_folder_name}, "Success", "Get iteration list:[{}:{}]".format(prj_name, _temp_folder_name))
    
    return success_msg(200, {"folder_name":folder_name}, "Success", "Get iteration list:[{}:{}]".format(prj_name, folder_name))

@app_cl_model.route('/<uuid>/get_model_info', methods=['POST']) 
@swag_from("{}/{}".format(YAML_PATH, "get_model_info.yml"))
def get_model_info(uuid):
    # Check uuid is/isnot in app.config["PROJECT_INFO"]
    if not ( uuid in app.config["PROJECT_INFO"].keys()):
        return error_msg(400, {}, "UUID:{} does not exist.".format(uuid), log=True)
    # Check key of front
    if not "iteration" in request.get_json().keys():
        return error_msg(400, {}, "KEY:iteration does not exist.", log=True)
    # Get project name
    prj_name = app.config["PROJECT_INFO"][uuid]["project_name"]
    # Get value of front
    front_iteration = request.get_json()['iteration']
    # Mapping iteration
    dir_iteration = chk.mapping_iteration(uuid, prj_name, front_iteration, front=True)
    if "error" in dir_iteration:
        return error_msg(400, {}, str(dir_iteration[1]), log=True)
    # Get model info from model database
    info_db = model_info_db(uuid, prj_name, dir_iteration)
    # Prevent error 
    if "error" in info_db:
        return error_msg(400, {}, str(info_db[1]))
    return success_msg(200, info_db, "Success", "Get infomation of model:[{}:{}]".format(prj_name, front_iteration))

@app_cl_model.route('/<uuid>/delete_iteration', methods=['DELETE'])
@swag_from("{}/{}".format(YAML_PATH, "delete_iteration.yml"))
def delete_iteration(uuid):
    # Check uuid is/isnot in app.config["PROJECT_INFO"]
    if not ( uuid in app.config["PROJECT_INFO"].keys()):
        return error_msg(400, {}, "UUID:{} does not exist.".format(uuid), log=True)
    # Check key of front
    if not "iteration" in request.get_json().keys():
        return error_msg(400, {}, "KEY:iteration does not exist.", log=True)
    # Get project name
    prj_name = app.config["PROJECT_INFO"][uuid]["project_name"]
    # Get value of front
    front_iteration = request.get_json()['iteration']
    # Mapping iteration
    prj_path = ROOT + "/" + prj_name
    dir_iteration = chk.mapping_iteration(uuid, prj_name, front_iteration, front=True)
    if "error" in dir_iteration:
        return error_msg(400, {}, str(dir_iteration[1]), log=True)
    iter_path = prj_path + "/" + dir_iteration
    if os.path.isdir(iter_path):
        # Delete iteration folder
        shutil.rmtree(iter_path)
        # Update app.config["MAPPING_ITERATION"]
        chk.update_mapping_name(prj_path, uuid)
        # Detele data from database
        error_db = del_model_db(uuid, dir_iteration)
        if error_db:
            return error_msg(400, {}, str(error_db[1]))
        return success_msg(200, {}, "Success", "Deleted iteration in the Project:[{}:{}]".format(prj_name, front_iteration))
    else:
        return error_msg(400, {} ,"This iteration does not exist in the Project:[{}:{}]".format(prj_name, front_iteration), log=True)

@app_cl_model.route('/<uuid>/curve_history', methods=['POST']) 
@swag_from("{}/{}".format(YAML_PATH, "curve_history.yml"))
def curve_history(uuid):
    # Check uuid is/isnot in app.config["PROJECT_INFO"]
    if not ( uuid in app.config["PROJECT_INFO"].keys()):
        return error_msg(400, {}, "UUID:{} does not exist.".format(uuid), log=True)
    # Check key of front
    if not "iteration" in request.get_json().keys():
        return error_msg(400, {}, "KEY:iteration does not exist.", log=True)
    # Get project name
    prj_name = app.config["PROJECT_INFO"][uuid]["project_name"]
    # Get value of front
    front_iteration = request.get_json()['iteration']
    # Mapping iteration
    dir_iteration = chk.mapping_iteration(uuid, prj_name, front_iteration, front=True)
    if "error" in dir_iteration:
        return error_msg(400, {}, str(dir_iteration[1]), log=True)
    iter_path = ROOT + "/" + prj_name + "/" + dir_iteration
    # Get log
    if os.path.isdir(iter_path):
        graph_path = iter_path + "/weights/graph.txt"
        if exists(graph_path):
            graph = {} 
            with open(graph_path) as file:
                for key,line in enumerate(file): 
                    json_acceptable_string = line.replace("'", "\"")
                    line = json.loads(json_acceptable_string)
                    graph.update({str(key+1):dict(line)})
            return success_msg(200, graph, "Success", "Get curve history of the Project:[{}:{}]".format(prj_name, front_iteration))
        else:
            return error_msg(400, {}, "This graph.txt does not exist in iteration of the Project:[{}:{}]".format(prj_name, front_iteration))
    else:
        return error_msg(400, {}, "This iteration does not exist in the Project:[{}:{}]".format(prj_name, front_iteration))
        
@app_cl_model.route('/<uuid>/metrics_history', methods=['POST']) 
@swag_from("{}/{}".format(YAML_PATH, "metrics_history.yml"))
def metrics_history(uuid):
    # Check uuid is/isnot in app.config["PROJECT_INFO"]
    if not ( uuid in app.config["PROJECT_INFO"].keys()):
        return error_msg(400, {}, "UUID:{} does not exist.".format(uuid), log=True)
    # Check key of front
    if not "iteration" in request.get_json().keys():
        return error_msg(400, {}, "KEY:iteration does not exist.", log=True)
    # Get project name
    prj_name = app.config["PROJECT_INFO"][uuid]["project_name"]
    # Get value of front
    front_iteration = request.get_json()['iteration']
    # Mapping iteration
    dir_iteration = chk.mapping_iteration(uuid, prj_name, front_iteration, front=True)
    if "error" in dir_iteration:
        return error_msg(400, {}, str(dir_iteration[1]), log=True)
    iter_path = ROOT + "/" + prj_name + "/" + dir_iteration
    if os.path.isdir(iter_path):
        metrics_path = iter_path + "/weights/metrics.json"
        if exists(metrics_path):
            metrics = read_json(metrics_path)
            return success_msg(200, metrics, "Success", "Get metrics history in iteration of the Project:[{}:{}]".format(prj_name, front_iteration))
        else:
            return error_msg(400, {}, "This metrics.json does not exist in iteration of the Project:[{}:{}]".format(prj_name, front_iteration))
    else:
        return error_msg(400, {}, "This iteration does not exist in the Project:[{}:{}]".format(prj_name, front_iteration))

@app_cl_model.route('/<uuid>/get_model_json', methods=['POST']) 
@swag_from("{}/{}".format(YAML_PATH, "get_model_json.yml"))
def get_model_json(uuid):
    # Check uuid is/isnot in app.config["PROJECT_INFO"]
    if not ( uuid in app.config["PROJECT_INFO"].keys()):
        return error_msg(400, {}, "UUID:{} does not exist.".format(uuid), log=True)
    # Check key of front
    if not "iteration" in request.get_json().keys():
        return error_msg(400, {}, "KEY:iteration does not exist.", log=True)
    # Get project name
    prj_name = app.config["PROJECT_INFO"][uuid]["project_name"]
    # Get type
    type = app.config["PROJECT_INFO"][uuid]["type"]
    # Get value of front
    front_iteration = request.get_json()['iteration']
    # Mapping iteration
    dir_iteration = chk.mapping_iteration(uuid, prj_name, front_iteration, front=True)
    if "error" in dir_iteration:
        return error_msg(400, {}, str(dir_iteration[1]), log=True)
    iter_path = ROOT + "/" + prj_name + "/" + dir_iteration
    # Select type
    if type == "object_detection":
        model = "yolo"
    else:
        model = "classification"
    if os.path.isdir(iter_path):
        # model.json
        train_param_path = iter_path+"/"+model+".json"
        model_param = {}
        if exists(train_param_path):
            train_param = read_json(train_param_path)
            model_param.update({"train_param":train_param})
        else:
            return error_msg("This model.json does not exist in iteration of the Project:[{}:{}]".format(prj_name, front_iteration))
        return success_msg(200, model_param, "Success", "Get training parameter in iteration of the Project:[{}:{}]".format(prj_name, front_iteration))
    else:
        return error_msg("This iteration does not exist in the Project:[{}:{}]".format(prj_name, front_iteration))

@app_cl_model.route('/<uuid>/check_best_model', methods=['POST']) 
@swag_from("{}/{}".format(YAML_PATH, "check_best_model.yml"))
def check_best_model(uuid):
    # Check uuid is/isnot in app.config["PROJECT_INFO"]
    if not ( uuid in app.config["PROJECT_INFO"].keys()):
        return error_msg(400, {}, "UUID:{} does not exist.".format(uuid), log=True)
    # Check key of front
    if not "iteration" in request.get_json().keys():
        return error_msg(400, {}, "KEY:iteration does not exist.", log=True)
    
    # Get project name
    prj_name = app.config["PROJECT_INFO"][uuid]["project_name"]
    # Get type
    type = app.config["PROJECT_INFO"][uuid]["type"]
    # Get value of front
    front_iteration = request.get_json()['iteration']
    # Mapping iteration
    dir_iteration = chk.mapping_iteration(uuid, prj_name, front_iteration, front=True)
    
    if "error" in dir_iteration:
        return error_msg(400, {}, str(dir_iteration[1]), log=True)
    
    #check wether on training or not.
    if app.config["SCHEDULE"].get_status(uuid,dir_iteration):
        return error_msg(400, {}, "The iteration of the Project:[{}:{}] is on training".format(prj_name, front_iteration), log=True)
    
    iter_path = ROOT + "/" + prj_name + "/" + dir_iteration
    if type == "object_detection":
        model = "yolo"
    else:
        model = "classification"
    if os.path.isdir(iter_path):
        # model.json
        train_param_path = iter_path + "/" + model + ".json"
        if exists(train_param_path):
            train_param = read_json(train_param_path)
            # Find best model path
            model_path = train_param["train_config"]["save_model_path"]
            best_list = [model for model in os.listdir(model_path) if "best" in model]
            if len(best_list) == 0:
                return error_msg(400, {}, "This best model does not exist in iteration of the Project:[{}:{}]".format(prj_name, front_iteration), log=True)
            else:
                return success_msg(200, {"Exist":True}, "Success", "This best model dose exist in iteration of the Project:[{}:{}]".format(prj_name, front_iteration))
        else:
            return error_msg("This model.json does not exist in iteration of the Project:[{}:{}]".format(prj_name, front_iteration))
    else:
        return error_msg("This iteration does not exist in the Project:[{}:{}]".format(prj_name, front_iteration))