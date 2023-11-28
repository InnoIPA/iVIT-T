from flask import Blueprint, request, jsonify
from flasgger import swag_from
import shutil, copy, time
from webapi import app
from .common.utils import success_msg, error_msg, write_json
from .common.config import ROOT, YAML_MAIN_PATH, METHOD_OF_TRAINING, TRAINING_CLASS, SOCKET_LISTENERS
from .common.training_tool import Fillin, create_iter_folder, Prepare_data, Training, cal_input_shape, cal_batch_size
from .common.inspection import Check, Pretrained
chk = Check()
app_train = Blueprint( 'training_model', __name__)
# Define API Docs path and Blue Print
YAML_PATH       = YAML_MAIN_PATH + "/training_model"

@app_train.route('/get_method_training', methods=['GET']) 
@swag_from("{}/{}".format(YAML_PATH, "get_method_training.yml"))
def get_method_training():
    method = METHOD_OF_TRAINING["classification"]["other"].keys()
    return success_msg(200, {"method_training": list(method)}, "Success")

@app_train.route('/<uuid>/get_model', methods=['GET']) 
@swag_from("{}/{}".format(YAML_PATH, "get_model.yml"))
def get_model(uuid):
    # Check uuid is/isnot in app.config["PROJECT_INFO"]
    if not ( uuid in app.config["PROJECT_INFO"].keys()):
        return error_msg(400, {}, "UUID:{} does not exist.".format(uuid), log=True)
    # Get platform
    platform = app.config["PROJECT_INFO"][uuid]["platform"]
    # Get type
    type = app.config["PROJECT_INFO"][uuid]["type"]
    # Platform filter
    if platform ==  "intel" or platform == "nvidia":
        platform = "other"
    # Get model option
    model = app.config['MODEL'][platform][type]
    return success_msg(200, {"model": model}, "Success")

@app_train.route('/<uuid>/get_batch_size', methods=['GET'])
@swag_from("{}/{}".format(YAML_PATH, "get_batch_size.yml")) 
def get_batch_size(uuid):
    # Check uuid is/isnot in app.config["PROJECT_INFO"]
    if not ( uuid in app.config["PROJECT_INFO"].keys()):
        return error_msg(400, {}, "UUID:{} does not exist.".format(uuid), log=True)
    # Get type
    type = app.config["PROJECT_INFO"][uuid]["type"]
    # Check batch_size of the optimization 
    batch_size = cal_batch_size(uuid, type)
    if "error" in batch_size:
        return error_msg(400, {}, str(batch_size[1]), log=True)
    return success_msg(200, {"batch_size": batch_size}, "Success")

@app_train.route('/<uuid>/get_default_param', methods=['POST']) 
@swag_from("{}/{}".format(YAML_PATH, "get_default_param.yml")) 
def get_default_param(uuid):
    # Check uuid is/isnot in app.config["PROJECT_INFO"]
    if not ( uuid in app.config["PROJECT_INFO"].keys()):
        return error_msg(400, {}, "UUID:{} does not exist.".format(uuid), log=True)
    # Check key of front
    if not "training_method" in request.get_json().keys():
        return error_msg(400, {}, "KEY:training_method does not exist.", log=True)
    # Get type
    type = app.config["PROJECT_INFO"][uuid]["type"]
    # Get platform
    platform = app.config["PROJECT_INFO"][uuid]["platform"]
    # Get value of front
    training_method = request.get_json()['training_method']
    # Platform filter
    if platform ==  "intel" or platform == "nvidia":
        platform = "other"
    # Get default param
    default = copy.deepcopy(METHOD_OF_TRAINING[type][platform][training_method])
    # Check batch_size of the optimization 
    batch_size = cal_batch_size(uuid, type)
    if "error" in batch_size:
        return error_msg(400, {}, str(batch_size[1]), log=True)
    if not default["batch_size"] in batch_size:
        default["batch_size"] = min(batch_size)
    # Suggest input_shape calculation
    default_db = cal_input_shape(default, uuid)
    if "error" in default_db:
        return error_msg(400, {}, str(default_db[1]))
    return success_msg(200, {"training_param":default_db}, "Success")

@app_train.route('/<uuid>/create_training_iter', methods=['POST']) 
@swag_from("{}/{}".format(YAML_PATH, "create_training_iter.yml"))
def create_training_iter(uuid):
    # Check uuid is/isnot in app.config["PROJECT_INFO"]
    if not ( uuid in app.config["PROJECT_INFO"].keys()):
        return error_msg(400, {}, "UUID:{} does not exist.".format(uuid), log=True)
    # Check key of front
    msg = chk.front_param_key(list(request.get_json().keys()), list(app.config['TRAINING_CONFIG']["front_train"].keys()))
    if msg:
        return error_msg(400, {}, "KEY:{} does not exist.".format(msg), log=True)
    # Check value in key of front
    msg = chk.front_param_isnull(request.get_json())
    if msg:
        return error_msg(400, {}, "KEY:{} is not filled in or the type is wrong.".format(msg), log=True)
    # Get project name
    prj_name = app.config["PROJECT_INFO"][uuid]["project_name"]
    # Get type
    model_type = app.config["PROJECT_INFO"][uuid]["type"]
    # --------------------------------------Fillin----------------------------------------------
    # Append to app.config["TRAINING_TASK"]
    app.config["TRAINING_TASK"].update({uuid:copy.deepcopy(app.config['TRAINING_CONFIG'])})
    fill_in = Fillin(uuid, model_type, prj_name)
    # Fill in app.config["TRAINING_TASK"][uuid]
    fill_in.fill_front_train(request.get_json())
    # Fill effect_img_nums
    fill_in.fill_effect_img()
    # Fill in app.config["TRAINING_TASK"][uuid][”model_param”]
    model_json = fill_in.fill_model_param()
    # ----------------------------------------Check--------------------------------------------
    # Check iteration folder can not over 20
    prj_path = ROOT + '/' + prj_name
    status, iter_max = chk.iter_twenty(prj_path, uuid)
    if status:
        del app.config["TRAINING_TASK"][uuid]
        return error_msg(400, {}, "This iteration is over 20 in the Project:[{}]".format(prj_name), log=True)
    # Create iteration folder and other folder
    iter_name = "iteration" + str(iter_max + 1)
    create_iter_folder(uuid, prj_name, iter_name)
    # Check image over 15 pic
    msg = chk.classes_images(uuid)
    if msg:
        del app.config["TRAINING_TASK"][uuid]
        shutil.rmtree('{}/{}/{}'.format(ROOT,prj_name, iter_name), ignore_errors=True)
        return error_msg(400, {}, "Class is not over 15 images:[{}]".format(msg), log=True)
    # -----------------------------------------Data-------------------------------------------
    try:
        # Update mapping iteration
        chk.update_mapping_name(prj_path, uuid)
        # Split dataset
        pdata = Prepare_data(uuid, prj_name, model_type, iter_name)
    except Exception as e:
        del app.config["TRAINING_TASK"][uuid]
        shutil.rmtree('{}/{}/{}'.format(ROOT,prj_name, iter_name), ignore_errors=True)
        return error_msg(400, {}, "Prepare data error! {}".format(e), log=True)
    
    # Append data to db
    error_db = pdata.append_database()
    if error_db:
        return error_msg(400, {}, str(error_db[1]))
    error_db = pdata.training_color_id_database()
    if error_db:
        return error_msg(400, {}, str(error_db[1]))

    # -----------------------------------------Fillin-------------------------------------------
    # For loop param use app.config["TRAINING_TASK"][uuid][”model_param”]
    stats = fill_in.fill_model_cfg()
    pre_trained = True
    # Pre-trained model does not exist.
    if "error" in stats:
        del app.config["TRAINING_TASK"][uuid]
        return error_msg(400, {}, str(stats[1]))
    if not stats[0]:
        pre_trained = False
    # Create new model.json
    model_param_path = prj_path + '/' + iter_name + '/' + model_json
    write_json(model_param_path, app.config["TRAINING_TASK"][uuid]['model_param'])
    # Append iteration name to app.config["TRAINING_TASK"][uuid]["iteration"]
    app.config["TRAINING_TASK"][uuid]["iteration"]["dir_name"] = iter_name
    app.config["TRAINING_TASK"][uuid]["iteration"]["front_name"] = app.config["MAPPING_ITERATION"][uuid][iter_name]
    front_info = {"iter_name":app.config["MAPPING_ITERATION"][uuid][iter_name], "prj_name":prj_name, "pre_trained":pre_trained}
    backend_info = {"iter_name":iter_name, "front_name":app.config["MAPPING_ITERATION"][uuid][iter_name], "prj_name":prj_name, "pre_trained":pre_trained}
    return success_msg(200, front_info, "Success", "Created training task:[{}]".format(backend_info))

@app_train.route('/<uuid>/start_training', methods=['GET'])
@swag_from("{}/{}".format(YAML_PATH, "start_training.yml"))
def start_training(uuid):
    training = Training()
    # Check uuid is/isnot in app.config["PROJECT_INFO"]
    if not ( uuid in app.config["PROJECT_INFO"].keys()):
        return error_msg(400, {}, "UUID:{} does not exist.".format(uuid), log=True)
    # Get project name
    prj_name = app.config["PROJECT_INFO"][uuid]["project_name"]
    # Get iteration name
    iter_name = app.config["TRAINING_TASK"][uuid]["iteration"]["dir_name"]
    # Get type
    type = app.config["PROJECT_INFO"][uuid]["type"]
    # Get model.json
    if type == "object_detection":
        model = "yolo"
    elif type == "classification":
        model = type
    # Run command
    command = 'python3 adapter.py -c {} --train'.format(ROOT + '/' +prj_name+'/'+ iter_name + '/'+ model + '.json')
    # Start training
    if not app.config["TRAINING_TASK"][uuid]['status']:
        # Recorded start_time
        app.config["TRAINING_TASK"][uuid]["start_time"] = time.time()
        TRAINING_CLASS.update({uuid:{"class":training}})
        app.config["TRAINING_TASK"][uuid]['status'] = training.thread_training(command, uuid, type, metrics=False)
        return success_msg(200, {}, "Success", 'Training of the Project:[{}:{}]'.format(prj_name, iter_name)) 
    else:
        return error_msg(400, {}, "Is running in training of the Project:[{}:{}]".format(prj_name, iter_name), log=True)

@app_train.route('/<uuid>/stop_training', methods=['GET']) 
@swag_from("{}/{}".format(YAML_PATH, "stop_training.yml"))
def stop_training(uuid):
    # Check uuid is/isnot in app.config["PROJECT_INFO"]
    if not ( uuid in app.config["PROJECT_INFO"].keys()):
        return error_msg(400, {}, "UUID:{} does not exist.".format(uuid), log=True)
    # Get project name
    prj_name = app.config["PROJECT_INFO"][uuid]["project_name"]
    # Get iteration name
    iter_name = app.config["TRAINING_TASK"][uuid]["iteration"]["dir_name"]
    # Check is running thread
    if len(TRAINING_CLASS[uuid]['class'].thread_list) > 0 and app.config["TRAINING_TASK"][uuid]['status']:
        # Stop training
        TRAINING_CLASS[uuid]['class'].thread_list[uuid]["stop"].set()
        return success_msg(200, {}, "Success", "Stop training in iteration of the Project:[{}:{}]".format(prj_name, iter_name))
    else:
        return error_msg(400, {}, "Threading does not exist in iteration of the Project:[{}:{}]".format(prj_name, iter_name), log=True)

@app_train.route('/<uuid>/download_pretrained', methods=['GET'])
@swag_from("{}/{}".format(YAML_PATH, "download_pretrained.yml"))
def download_pretrained(uuid):
    # Check uuid is/isnot in app.config["PROJECT_INFO"]
    if not ( uuid in app.config["PROJECT_INFO"].keys()):
        return error_msg(400, {}, "UUID:{} does not exist.".format(uuid), log=True)
    # Get type
    type = app.config["PROJECT_INFO"][uuid]["type"]
    # Get iteration name
    arch = app.config["TRAINING_TASK"][uuid]["model_param"]["model_config"]["arch"]
    # Download pre-trained model
    pretrained = Pretrained()
    pretrained.download_pretrained(arch, type, uuid)
    return success_msg(200, {}, "Success")

@app_train.route('/get_training_task', methods=['GET'])
@swag_from("{}/{}".format(YAML_PATH, "get_training_task.yml"))
def get_training_task():
    return success_msg(200, app.config["TRAINING_TASK"], "Success", "Get information from app.config['TRAINING_TASK']")

@app_train.route('/get_mapping_iteration', methods=['GET'])
@swag_from("{}/{}".format(YAML_PATH, "get_mapping_iteration.yml"))
def get_mapping_iteration():
    return success_msg(200, app.config["MAPPING_ITERATION"], "Success", "Get information from app.config['MAPPING_ITERATION']")

@app_train.route('/prj_training_status', methods=['GET'])
@swag_from("{}/{}".format(YAML_PATH, "prj_training_status.yml"))
def prj_training_status():
    stats = {}
    if len(app.config['TRAINING_TASK'].keys()) > 0:
        for key in app.config['TRAINING_TASK'].keys():
            stats[key] = {"iteration":"", "status":False}
            stats[key]['iteration'] = app.config['TRAINING_TASK'][key]['iteration']['front_name']
            stats[key]['status'] = app.config['TRAINING_TASK'][key]['status']
    return success_msg(200, stats, "Success", "Get infomation from app.config['TRAINING_TASK']")

@app_train.route('/socket_listen_list', methods=['GET'])
@swag_from("{}/{}".format(YAML_PATH, "socket_listen_list.yml"))
def socket_listen_list():
    return success_msg(200, SOCKET_LISTENERS, "Success", "Get socket_listen_list")

@app_train.route('/training_schedule', methods=['POST']) 
@swag_from("{}/{}".format(YAML_PATH, "add_task.yml"))
def add_task():
    train_parameter = request.get_json()["training_parameter"]
    # Check key of front
    msg = chk.front_param_key(list(train_parameter.keys()), list(app.config['TRAINING_CONFIG']["front_train"].keys()))
    if msg:
        return error_msg(400, {}, "KEY:{} does not exist.".format(msg), log=True)
    # Check value in key of front
    msg = chk.front_param_isnull(train_parameter)
    if msg:
        return error_msg(400, {}, "KEY:{} is not filled in or the type is wrong.".format(msg), log=True)

    add_task_info = app.config["SCHEDULE"].add_task(request.get_json())

    if isinstance(add_task_info,str) and ("error" in add_task_info):
        return error_msg(400, {}, "Add task error! error msg:{}.".format(add_task_info), log=True)
    
    return success_msg(200,{"task_uuid":add_task_info}, "Success", "Add task suuccess. task_uuid={}".format(add_task_info))


@app_train.route('/training_schedule', methods=['PUT']) 
@swag_from("{}/{}".format(YAML_PATH, "modify_task_list.yml"))
def modify_task_list():
    try:    
        task_sort = request.get_json()["task_sort"]
    except:
        return error_msg(400, {}, "Key:task_sort error.", log=True)
    
    if (not task_sort) or (not isinstance(task_sort,list)): 
        return error_msg(400, {}, "Modify task list error! please check task_sort.", log=True)
    
    task_list_info = app.config["SCHEDULE"].modify_task_list(task_sort)
    if isinstance(task_list_info,str) and ("error" in task_list_info):
        return error_msg(400, {}, "Modify task list error! error msg:{}.".format(task_list_info), log=True)
    return success_msg(200, {"task_list":task_list_info}, "Success", "Get task list:{}".format(str(task_list_info)))

@app_train.route('/training_schedule', methods=['GET']) 
@swag_from("{}/{}".format(YAML_PATH, "get_task.yml"))
def get_task():
    sort = app.config["SCHEDULE"].task_sort
    if not sort:
        return error_msg(400, {}, "No task in schedule.", log=True)
    get_task_info = app.config["SCHEDULE"]._get_task_sort_detail(sort)
    
    return success_msg(200, {"task_list":get_task_info}, "Success", "Get task sort success! result:{}".format(get_task_info))

@app_train.route('/training_schedule', methods=['DELETE']) 
@swag_from("{}/{}".format(YAML_PATH, "delete_task.yml"))
def delete_task():
    try:    
        task_uuid = request.get_json()["task_uuid"]
    except:
        return error_msg(400, {}, "Key:task_uuid error!.", log=True)
    
    delete_task_info = app.config["SCHEDULE"].delete_task(task_uuid)

    if isinstance(delete_task_info,str) and ("error" in delete_task_info):
        return error_msg(400, {}, "Delete task error! error msg:{}.".format(delete_task_info), log=True)
    
    return success_msg(200, {}, "Success", "Delete task:{} success!".format(delete_task_info))

@app_train.route('/stop_task', methods=['POST']) 
@swag_from("{}/{}".format(YAML_PATH, "stop_task.yml"))
def stop_task():
    try:    
        task_uuid = request.get_json()["task_uuid"]
    except:
        return error_msg(400, {}, "Key:task_uuid error!.", log=True)
    
    stop_task_info = app.config["SCHEDULE"].stop_task(task_uuid)
    if isinstance(stop_task_info,str) and ("error" in stop_task_info):
        return error_msg(400, {}, "Stop task error! error msg:{}.".format(stop_task_info), log=True)

    return success_msg(200, {}, "Success", "Stop task:{} success!".format(stop_task_info))

@app_train.route('/history', methods=['DELETE']) 
@swag_from("{}/{}".format(YAML_PATH, "delete_history.yml"))
def delete_history():
    try:    
        task_uuid = request.get_json()["task_uuid"]
    except:
        return error_msg(400, {}, "Key:task_uuid error!.", log=True)
    
    delete_history_info = app.config["SCHEDULE"]._delete_history(task_uuid)
    if isinstance(delete_history_info,str) and ("error" in delete_history_info):
        return error_msg(400, {}, "Delete history error! error msg:{}.".format(delete_history_info), log=True)
    
    return success_msg(200, {}, "Success", "Delete_history:{} success!".format(delete_history_info))

@app_train.route('/history', methods=['GET']) 
@swag_from("{}/{}".format(YAML_PATH, "get_history.yml"))
def get_history():
    history_info = app.config["SCHEDULE"]._get_all_history(True)
    if isinstance(history_info,str) and ("error" in history_info):
        return error_msg(400, {}, "Delete history error! error msg:{}.".format(history_info), log=True)
    
    return success_msg(200, {"history_list":history_info}, "Success", "Get history list success! result:{}".format(history_info))