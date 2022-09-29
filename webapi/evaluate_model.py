from flask import Blueprint, request, jsonify
from flasgger import swag_from
import logging
import os, shutil
from webapi import app
from werkzeug.utils import secure_filename
from .common.utils import error_msg, ALLOWED_EXTENSIONS, exists, success_msg, YAML_MAIN_PATH
from .common.training_tool import Fillin
from .common.evaluate_tool import set_eval_json, eval_cmd
from .common.labeling_tool import save_bbox
fill_in = Fillin()

app_eval = Blueprint( 'evaluate_model', __name__)
# Define API Docs path and Blue Print
YAML_PATH       = YAML_MAIN_PATH + "/evaluate_model"

@app_eval.route('/<uuid>/upload_eval_img', methods=['POST']) 
@swag_from("{}/{}".format(YAML_PATH, "upload_eval_img.yml"))
def upload_eval_img(uuid):
    if request.method == 'POST':
        # Check uuid is/isnot in app.config["PROJECT_INFO"]
        if not ( uuid in app.config["PROJECT_INFO"].keys()):
            return error_msg("UUID:{} is not exist.".format(uuid))
        # Check key of front
        if not "iteration" in request.form.keys():
            return error_msg("KEY:iteration is not exist.")
        # Get project name
        prj_name = app.config["PROJECT_INFO"][uuid]["front_project"]["project_name"]
        # Get value of front
        iteration = request.form.get('iteration')
        # Save path
        save_path = "./Project/"+ prj_name + "/" + iteration + "/dataset/eval"
        # Remove folder all file
        shutil.rmtree(save_path)
        os.mkdir(save_path)

        img_list = []
        # files is multi folder 
        for key in request.files.keys():
            # Get files in files.getlist
            files = request.files.getlist(key)
            # if is empty
            if not files:
                return error_msg("No upload files.")
            # Get filename in files
            for idx, file in enumerate(files):
                if file and idx < 10:
                    # Get file name
                    filename = secure_filename(file.filename)
                    # Skip other format exclude image format
                    if not (filename.split(".")[-1] in ALLOWED_EXTENSIONS["image"]):
                        continue
                    # Save image
                    file.save(os.path.join(save_path, "eval_" + str(idx)+ "." + filename.split(".")[-1]))
                    img_path = save_path+"/"+"eval_" + str(idx) + "." + filename.split(".")[-1]
                    # Append to list
                    if exists(img_path):
                        img_list.append(img_path)
                else:
                    logging.error("Upload file is over 10 images, image_name:{}".format(file.filename))
        return jsonify({"eval_img":img_list})

@app_eval.route('/<uuid>/evaluate', methods=['POST']) 
@swag_from("{}/{}".format(YAML_PATH, "evaluate.yml")) 
def evaluate(uuid):
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
        # Setting config.json
        fill_in.set_config_json(prj_name, iteration, type)
        # Setting evaluate.json
        status, msg = set_eval_json(prj_name, iteration)
        if not status:
            return error_msg(msg + ", Project:{}, iteration:{}".format(prj_name, iteration))
        # Evaluate
        command = "python3 evaluate.py"
        # Run command
        log_dict = eval_cmd(type, command)
        
    return jsonify({"detections":log_dict})

@app_eval.route('/<uuid>/recheck_bbox', methods=['POST']) 
@swag_from("{}/{}".format(YAML_PATH, "recheck_bbox.yml")) 
def recheck_bbox(uuid):
    if request.method == 'POST':
        # Check uuid is/isnot in app.config["PROJECT_INFO"]
        if not ( uuid in app.config["PROJECT_INFO"].keys()):
            return error_msg("UUID:{} is not exist.".format(uuid))
        # Check key of front
        if not "iteration" in request.get_json().keys(): 
            return error_msg("KEY:iteration is not exist.")
        elif not "image_name" in request.get_json().keys():
            return error_msg("KEY:image_name is not exist.")
        elif not "box_info" in request.get_json().keys(): 
            return error_msg("KEY:box_info is not exist.")
        # Get project name
        prj_name = app.config["PROJECT_INFO"][uuid]["front_project"]["project_name"]
        # Get value of front
        iteration = request.get_json()['iteration']
        image_name = request.get_json()['image_name']
        box_info = request.get_json()['box_info']
        # Move image to dataset
        img_path = "./Project/"+prj_name+"/"+iteration+"/dataset/eval/"+image_name
        save_path = "./Project/"+prj_name+"/workspace/"
        if exists(img_path):
            shutil.copyfile(img_path, save_path+"/"+image_name)
            save_bbox(save_path+"/"+image_name, box_info)
            return success_msg("Save image:{} and box:{} in dataset of Project:{}".format(image_name, box_info, prj_name))
        else:
            return error_msg("This image:{} is not exist in Project:{}".format(image_name, prj_name))

@app_eval.route('/<uuid>/recheck_class', methods=['POST']) 
@swag_from("{}/{}".format(YAML_PATH, "recheck_class.yml")) 
def recheck_class(uuid):
    if request.method == 'POST':
        # Check uuid is/isnot in app.config["PROJECT_INFO"]
        if not ( uuid in app.config["PROJECT_INFO"].keys()):
            return error_msg("UUID:{} is not exist.".format(uuid))
        # Check key of front
        if not "iteration" in request.get_json().keys(): 
            return error_msg("KEY:iteration is not exist.")
        elif not "image_name" in request.get_json().keys():
            return error_msg("KEY:image_name is not exist.")
        elif not "class_name" in request.get_json().keys():
            return error_msg("KEY:class_name is not exist.")
        # Get project name
        prj_name = app.config["PROJECT_INFO"][uuid]["front_project"]["project_name"]
        # Get value of front 
        iteration = request.get_json()['iteration']
        image_name = request.get_json()['image_name']
        class_name = request.get_json()['class_name'] 
        # Move image to dataset
        img_path = "./Project/"+prj_name+"/"+iteration+"/dataset/eval/"+image_name
        save_path = "./Project/"+prj_name+"/workspace/"+class_name
        if exists(img_path):
            shutil.copyfile(img_path, save_path+"/"+image_name)
            return success_msg("Save image:{} and label:{} in dataset of Project:{}".format(image_name, class_name, prj_name))
        else:
            return error_msg("This image:{} is not exist in Project:{}".format(image_name, prj_name))