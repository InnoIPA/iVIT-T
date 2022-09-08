from flask import Blueprint, request, jsonify
from flasgger import swag_from
# import logging
import shutil
from webapi import app
from .common.utils import success_msg, error_msg, write_json
from .common.training_tool import METHOD_OF_TRAINING, BATCH_SIZE, Fillin, create_iter_folder, Prepare_data, Training
from .common.inspection import Check
chk = Check()
fill_in = Fillin()
training = Training()

app_train = Blueprint( 'train_model', __name__)
app.config['NEW_TRAIN_CONFIG'] = {"front_train":{
                                        "export_platform":"",
                                        "model": "",
                                        "batch_size": None,
                                        "step": None,
                                        "input_shape": [
                                            None,
                                            None,
                                            None
                                        ],
                                        "spend_time":"",
                                        "training_method":"",
                                        "GPU":[""],
                                        "effect_img_num":None
                                        },
                        "model_param":{},
                        "remaining_time":None}
EXCEPT_LIST = ["export_platform","GPU","effect_img_num", "spend_time"]

@app_train.route('/get_method_training', methods=['GET']) 
@swag_from('./descript/train_model/get_method_training.yml')
def get_method_training():
    method = METHOD_OF_TRAINING["classification"]["other"].keys()

    return jsonify({"method_training": list(method)})

@app_train.route('/<uuid>/get_model', methods=['GET']) 
@swag_from('./descript/train_model/get_model.yml')
def get_model(uuid):
    # Check uuid is/isnot in app.config["PROJECT_INFO"]
    if not ( uuid in app.config["PROJECT_INFO"].keys()):
        return error_msg("UUID:{} is not exist.".format(uuid))
    # Get platform
    platform = app.config["PROJECT_INFO"][uuid]["front_project"]["platform"]
    # Get type
    type = app.config["PROJECT_INFO"][uuid]["front_project"]["type"]
    
    # platform == intel or nvidia
    if platform ==  "intel" or platform == "nvidia":
        platform = "other"

    # Get model option
    model = app.config['MODEL'][platform][type]

    return jsonify({"model": model})

@app_train.route('/<uuid>/get_batch_size', methods=['GET']) 
@swag_from('./descript/train_model/get_batch_size.yml')
def get_batch_size(uuid):
    # Check uuid is/isnot in app.config["PROJECT_INFO"]
    if not ( uuid in app.config["PROJECT_INFO"].keys()):
        return error_msg("UUID:{} is not exist.".format(uuid))
    # Get classes_num
    classes_num = len(app.config["PROJECT_INFO"][uuid]["front_project"]["classes_num"])
    # Get effect_img_num
    effect_img_num = app.config["PROJECT_INFO"][uuid]["front_project"]["effect_img_num"]
    # Calculate max batch
    max_batch = int((effect_img_num // classes_num)*0.1)
    batch_size = [ batch for batch in BATCH_SIZE if batch <= max_batch]

    return jsonify({"batch_size": batch_size})

@app_train.route('/<uuid>/get_default_param', methods=['POST']) 
@swag_from('./descript/train_model/get_default_param.yml')
def get_default_param(uuid):
    if request.method == 'POST':
        # Check uuid is/isnot in app.config["PROJECT_INFO"]
        if not ( uuid in app.config["PROJECT_INFO"].keys()):
            return error_msg("UUID:{} is not exist.".format(uuid))
        # Check key of front
        if not "training_method" in request.get_json().keys():
            return error_msg("KEY:training_method is not exist.")
        # Get type
        type = app.config["PROJECT_INFO"][uuid]["front_project"]["type"]
        # Get platform
        platform = app.config["PROJECT_INFO"][uuid]["front_project"]["platform"]
        # Get value of front
        training_method = request.get_json()['training_method']

        # platform == intel or nvidia
        if platform ==  "intel" or platform == "nvidia":
            platform = "other"

        # Get default param
        default = METHOD_OF_TRAINING[type][platform][training_method]

        return jsonify({"training_param":default})

@app_train.route('/<uuid>/create_training_iter', methods=['POST']) 
@swag_from('./descript/train_model/create_training_iter.yml')
def create_training_iter(uuid):
    if request.method == 'POST':
        # Check uuid is/isnot in app.config["PROJECT_INFO"]
        if not ( uuid in app.config["PROJECT_INFO"].keys()):
            return error_msg("UUID:{} is not exist.".format(uuid))
        # Check key of front
        status, msg = chk.front_param_key(list(request.get_json().keys()), list(app.config['NEW_TRAIN_CONFIG']["front_train"].keys()), EXCEPT_LIST)
        if not status:
            return error_msg("KEY:{} is not exist.".format(msg))
        # Check value in key of front
        status, msg = chk.front_param_isnull(request.get_json())
        if not status:
            return error_msg("KEY:{} is not fill in.".format(msg))
        # Get project name
        prj_name = app.config["PROJECT_INFO"][uuid]["front_project"]["project_name"]
        # Get type
        type = app.config["PROJECT_INFO"][uuid]["front_project"]["type"]
        # Fill in app.config['NEW_TRAIN_CONFIG'][”front_train”]
        fill_in.fill_front_train(request.get_json())
        # Fill effect_img_num
        fill_in.fill_effect_img(uuid)
        # Fill in app.config['NEW_TRAIN_CONFIG'][”model_param”]
        model_json = fill_in.fill_model_param(type)
        # Check iteration folder can not over 20
        prj_path = "./Project/"+prj_name
        status, iter_len = chk.iter_twenty(prj_path)
        if status:
            return error_msg("This iteration is over 20 in Project:{}".format(prj_name))
        # Create iteration folder and other folder
        iter_name = "iteration"+str(iter_len+1)
        create_iter_folder(prj_name, iter_name)
        # Check image over 15 pic
        status, msg = chk.classes_images(uuid)
        if not status:
            shutil.rmtree('./Project/{}/{}'.format(prj_name,iter_name), ignore_errors=True)
            return error_msg("Class:{} is not over 15 images.".format(msg))
        # Split dataset
        Prepare_data(prj_name, type)
        # For loop param use app.config['NEW_TRAIN_CONFIG'][”model_param”]
        fill_in.fill_model_cfg(uuid)
        # Create new model.json and front_train.json
        front_train_path = prj_path + '/' + iter_name + '/front_train.json'
        model_param_path = prj_path + '/' + iter_name + '/' + model_json
        write_json(front_train_path, app.config['NEW_TRAIN_CONFIG']['front_train'])
        write_json(model_param_path, app.config['NEW_TRAIN_CONFIG']['model_param'])

        # Setting main training Config.json
        fill_in.set_config_json(prj_name, iter_name, type)
        # Append training info to app.config["PROJECT_INFO"][uuid]["training_info"]["iteration"]
        # This training_info action can aviod all global varity to change, only fouse uuid project 
        app.config["PROJECT_INFO"][uuid]["training_info"] = {"iteration":"","status":False}
        app.config["PROJECT_INFO"][uuid]["training_info"]["iteration"] = iter_name
        # Append training param to app.config["PROJECT_INFO"][uuid]["training_info"]
        app.config["PROJECT_INFO"][uuid]["training_info"].update(app.config['NEW_TRAIN_CONFIG'])
        return jsonify({"iter_name":iter_name,"prj_name":prj_name})
        # return success_msg("Finished setting up parameter of the training model in {} of Project:{}".format(iter_name, prj_name))

@app_train.route('/<uuid>/start_training', methods=['GET']) 
@swag_from('./descript/train_model/start_training.yml')
def start_training(uuid):
    # Check uuid is/isnot in app.config["PROJECT_INFO"]
    if not ( uuid in app.config["PROJECT_INFO"].keys()):
        return error_msg("UUID:{} is not exist.".format(uuid))
    # Get project name
    prj_name = app.config["PROJECT_INFO"][uuid]["front_project"]["project_name"]
    # Get iteration name
    iter_name = app.config["PROJECT_INFO"][uuid]["training_info"]["iteration"]
    # Run command
    command = 'python3 train.py'
    # Start training
    if not app.config['PROJECT_INFO'][uuid]['training_info']['status']:
        app.config['PROJECT_INFO'][uuid]['training_info']['status'] = training.thread_training(command, uuid)
        return success_msg('Training in iteration:{} of Project:{}'.format(iter_name, prj_name)) 
    else:
        return error_msg("Is running in iteration:{} of Project:{}".format(iter_name, prj_name))

@app_train.route('/<uuid>/stop_training', methods=['GET']) 
@swag_from('./descript/train_model/stop_training.yml')
def stop_training(uuid):
    # Check uuid is/isnot in app.config["PROJECT_INFO"]
    if not ( uuid in app.config["PROJECT_INFO"].keys()):
        return error_msg("UUID:{} is not exist.".format(uuid))
    # Get project name
    prj_name = app.config["PROJECT_INFO"][uuid]["front_project"]["project_name"]
    # Get iteration name
    iter_name = app.config["PROJECT_INFO"][uuid]["training_info"]["iteration"]
    # Check is running thread
    if len(training.thread_list) > 0 and app.config['PROJECT_INFO'][uuid]["training_info"]["status"]:
        training.thread_list[uuid]["stop"].set()
        # Clean global variable
        app.config["PROJECT_INFO"][uuid]["training_info"] = {"iteration":"","status":False}
        return success_msg("Stop training in iteration:{} of Project:{}".format(iter_name, prj_name))
    else:
        return error_msg("Thread is not exist in iteration:{} of Project:{}".format(iter_name, prj_name))

@app_train.route('/<uuid>/get_training_info', methods=['GET']) 
@swag_from('./descript/train_model/get_training_info.yml')
def get_training_info(uuid):
    # Check uuid is/isnot in app.config["PROJECT_INFO"]
    if not ( uuid in app.config["PROJECT_INFO"].keys()):
        return error_msg("UUID:{} is not exist.".format(uuid))
    # Get effect_img_num
    effect_img_num = app.config["PROJECT_INFO"][uuid]["front_project"]["effect_img_num"]
    # Get training_method
    if not ("front_train" in app.config["PROJECT_INFO"][uuid]["training_info"].keys()):
        return error_msg("uuid:{} is not training".format(uuid))
    training_method = app.config["PROJECT_INFO"][uuid]["training_info"]["front_train"]["training_method"]
    # Get remaining_time
    remaining_time = app.config["PROJECT_INFO"][uuid]["training_info"]["remaining_time"]

    return jsonify({"effect_img_num":effect_img_num, "training_method":training_method, "remaining_time":remaining_time})