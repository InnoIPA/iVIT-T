from flask import Blueprint, request, jsonify
from flasgger import swag_from
import shutil, logging, copy, time
from webapi import app
from .common.utils import success_msg, error_msg, write_json, exists, read_txt
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

    return jsonify({"method_training": list(method)})

@app_train.route('/<uuid>/get_model', methods=['GET']) 
@swag_from("{}/{}".format(YAML_PATH, "get_model.yml"))
def get_model(uuid):
    # Check uuid is/isnot in app.config["PROJECT_INFO"]
    if not ( uuid in app.config["PROJECT_INFO"].keys()):
        return error_msg("UUID:{} does not exist.".format(uuid))
    # Get platform
    platform = app.config["PROJECT_INFO"][uuid]["platform"]
    # Get type
    type = app.config["PROJECT_INFO"][uuid]["type"]
    # Platform filter
    if platform ==  "intel" or platform == "nvidia":
        platform = "other"
    # Get model option
    model = app.config['MODEL'][platform][type]
    return jsonify({"model": model})

@app_train.route('/<uuid>/get_batch_size', methods=['GET'])
@swag_from("{}/{}".format(YAML_PATH, "get_batch_size.yml")) 
def get_batch_size(uuid):
    # Check uuid is/isnot in app.config["PROJECT_INFO"]
    if not ( uuid in app.config["PROJECT_INFO"].keys()):
        return error_msg("UUID:{} does not exist.".format(uuid))
    # Get type
    type = app.config["PROJECT_INFO"][uuid]["type"]
    # Check batch_size of the optimization 
    batch_size = cal_batch_size(uuid, type)
    return jsonify({"batch_size": batch_size})

@app_train.route('/<uuid>/get_default_param', methods=['POST']) 
@swag_from("{}/{}".format(YAML_PATH, "get_default_param.yml")) 
def get_default_param(uuid):
    if request.method == 'POST':
        # Check uuid is/isnot in app.config["PROJECT_INFO"]
        if not ( uuid in app.config["PROJECT_INFO"].keys()):
            return error_msg("UUID:{} does not exist.".format(uuid))
        # Check key of front
        if not "training_method" in request.get_json().keys():
            return error_msg("KEY:training_method does not exist.")
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
        if not default["batch_size"] in batch_size:
            default["batch_size"] = min(batch_size)
        # Suggest input_shape calculation
        default = cal_input_shape(default, uuid)
        if "error" in default:
            return error_msg(str(default[1]))
        return jsonify({"training_param":default})

@app_train.route('/<uuid>/create_training_iter', methods=['POST']) 
@swag_from("{}/{}".format(YAML_PATH, "create_training_iter.yml"))
def create_training_iter(uuid):
    if request.method == 'POST':
        # Check uuid is/isnot in app.config["PROJECT_INFO"]
        if not ( uuid in app.config["PROJECT_INFO"].keys()):
            return error_msg("UUID:{} does not exist.".format(uuid))
        # Check key of front
        status, msg = chk.front_param_key(list(request.get_json().keys()), list(app.config['TRAINING_CONFIG']["front_train"].keys()))
        if not status:
            return error_msg("KEY:{} does not exist.".format(msg))
        # Check value in key of front
        status, msg = chk.front_param_isnull(request.get_json())
        if not status:
            return error_msg("KEY:{} is not filled in or the type is wrong.".format(msg))
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
            return error_msg("This iteration is over 20 in Project:{}".format(prj_name))
        # Create iteration folder and other folder
        iter_name = "iteration" + str(iter_max + 1)
        create_iter_folder(uuid, prj_name, iter_name)
        # Check image over 15 pic
        status, msg = chk.classes_images(uuid)
        if not status:
            del app.config["TRAINING_TASK"][uuid]
            shutil.rmtree('{}/{}/{}'.format(ROOT,prj_name, iter_name), ignore_errors=True)
            return error_msg("Class:{} is not over 15 images.".format(msg))
        # -----------------------------------------Fillin-------------------------------------------
        # For loop param use app.config["TRAINING_TASK"][uuid][”model_param”]
        stats, msg = fill_in.fill_model_cfg()
        pre_trained = True
        # Pre-trained model does not exist.
        if not stats:
            if msg == "arch":
                pre_trained = False
            else:
                del app.config["TRAINING_TASK"][uuid]
                shutil.rmtree('{}/{}/{}'.format(ROOT,prj_name, iter_name), ignore_errors=True)
                return error_msg("The input shape is wrong.")
                
        elif type(stats) == list:
            return error_msg(str(stats[1]))
        # -----------------------------------------Data-------------------------------------------
        # Update mapping table
        chk.update_mapping_name(prj_path, uuid)
        # Split dataset
        pdata = Prepare_data(uuid, prj_name, model_type, iter_name)
        # Append data to db
        info_db = pdata.append_database()
        if info_db is not None:
            return error_msg(str(info_db[1]))

        # Create new model.json
        model_param_path = prj_path + '/' + iter_name + '/' + model_json
        write_json(model_param_path, app.config["TRAINING_TASK"][uuid]['model_param'])
        # Append iteration name to app.config["TRAINING_TASK"][uuid]["iteration"]
        app.config["TRAINING_TASK"][uuid]["iteration"]["dir_name"] = iter_name
        app.config["TRAINING_TASK"][uuid]["iteration"]["front_name"] = app.config["MAPPING_ITERATION"][uuid][iter_name]
        logging.info("Created training task:[{}]".format({"iter_name":iter_name, "front_name":app.config["MAPPING_ITERATION"][uuid][iter_name], 
                                                            "prj_name":prj_name, "pre_trained":pre_trained}))
        return jsonify({"iter_name":app.config["MAPPING_ITERATION"][uuid][iter_name], "prj_name":prj_name, "pre_trained":pre_trained})

@app_train.route('/<uuid>/start_training', methods=['GET'])
@swag_from("{}/{}".format(YAML_PATH, "start_training.yml"))
def start_training(uuid):
    training = Training()
    # Check uuid is/isnot in app.config["PROJECT_INFO"]
    if not ( uuid in app.config["PROJECT_INFO"].keys()):
        return error_msg("UUID:{} does not exist.".format(uuid))
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
    command = 'python3 train.py -c {}'.format(ROOT + '/' +prj_name+'/'+ iter_name + '/'+ model + '.json')
    # Start training
    if not app.config["TRAINING_TASK"][uuid]['status']:
        # Recorded start_time
        app.config["TRAINING_TASK"][uuid]["start_time"] = time.time()
        TRAINING_CLASS.update({uuid:{"class":training}})
        app.config["TRAINING_TASK"][uuid]['status'] = training.thread_training(command, uuid, type, metrics=False)
        return success_msg('Training in iteration:{} of Project:{}'.format(iter_name, prj_name)) 
    else:
        return error_msg("Is running in iteration:{} of Project:{}".format(iter_name, prj_name))

@app_train.route('/<uuid>/stop_training', methods=['GET']) 
@swag_from("{}/{}".format(YAML_PATH, "stop_training.yml"))
def stop_training(uuid):
    # Check uuid is/isnot in app.config["PROJECT_INFO"]
    if not ( uuid in app.config["PROJECT_INFO"].keys()):
        return error_msg("UUID:{} does not exist.".format(uuid))
    # Get project name
    prj_name = app.config["PROJECT_INFO"][uuid]["project_name"]
    # Get iteration name
    iter_name = app.config["TRAINING_TASK"][uuid]["iteration"]["dir_name"]
    # Check is running thread
    if uuid in list(TRAINING_CLASS.keys()):
        if len(TRAINING_CLASS[uuid]['class'].thread_list) > 0 and app.config["TRAINING_TASK"][uuid]['status']:
            # Stop training
            TRAINING_CLASS[uuid]['class'].thread_list[uuid]["stop"].set()
            return success_msg("Stop training in iteration:[{}] of Project:[{}]".format(iter_name, prj_name))
    else:
        return error_msg("Thread does not exist in iteration:[{}] of Project:[{}]".format(iter_name, prj_name))

@app_train.route('/<uuid>/download_pretrained', methods=['GET'])
@swag_from("{}/{}".format(YAML_PATH, "download_pretrained.yml"))
def download_pretrained(uuid):
    # Check uuid is/isnot in app.config["PROJECT_INFO"]
    if not ( uuid in app.config["PROJECT_INFO"].keys()):
        return error_msg("UUID:{} does not exist.".format(uuid))
    # Get iteration name
    arch = app.config["TRAINING_TASK"][uuid]["model_param"]["model_config"]["arch"]
    # Get type
    type = app.config["PROJECT_INFO"][uuid]["type"]
    # Download pre-trained model
    pretrained = Pretrained()
    pretrained.download_pretrained(arch, type, uuid)

    return success_msg("True")

@app_train.route('/get_training_task', methods=['GET'])
@swag_from("{}/{}".format(YAML_PATH, "get_training_task.yml"))
def get_training_task():
    logging.info("Get information from app.config['TRAINING_TASK']!")
    return app.config["TRAINING_TASK"]

@app_train.route('/get_mapping_iteration', methods=['GET'])
@swag_from("{}/{}".format(YAML_PATH, "get_mapping_iteration.yml"))
def get_mapping_iteration():
    logging.info("Get information from app.config['MAPPING_ITERATION']!")
    return app.config["MAPPING_ITERATION"]

@app_train.route('/prj_training_status', methods=['GET'])
@swag_from("{}/{}".format(YAML_PATH, "prj_training_status.yml"))
def prj_training_status():
    logging.info("Get information from app.config['TRAINING_TASK']!")
    stats = {}
    if len(app.config['TRAINING_TASK'].keys()) > 0:
        for key in app.config['TRAINING_TASK'].keys():
            stats[key] = {"iteration":"", "status":False}
            stats[key]['iteration'] = app.config['TRAINING_TASK'][key]['iteration']['front_name']
            stats[key]['status'] = app.config['TRAINING_TASK'][key]['status']
    return stats

@app_train.route('/socket_listen_list', methods=['GET'])
@swag_from("{}/{}".format(YAML_PATH, "socket_listen_list.yml"))
def socket_listen_list():
    logging.info("Get socket_listen_list!")
    return jsonify(SOCKET_LISTENERS)