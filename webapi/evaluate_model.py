from flask import Blueprint, request, jsonify
from flasgger import swag_from
import logging, os, shutil, random, string
from webapi import app
from werkzeug.utils import secure_filename
from .common.utils import error_msg, exists, success_msg, regular_expression
from .common.config import ALLOWED_EXTENSIONS, ROOT, YAML_MAIN_PATH, EVAL_VAL
from .common.inspection import Check
from .common.upload_tool import Upload_DB
from .common.evaluate_tool import Evaluate, threshold_process
from .common.labeling_tool import save_bbox
chk = Check()
app_eval = Blueprint( 'evaluate_model', __name__)
# Define API Docs path and Blue Print
YAML_PATH       = YAML_MAIN_PATH + "/evaluate_model"

@app_eval.route('/<uuid>/upload_eval_img', methods=['POST']) 
@swag_from("{}/{}".format(YAML_PATH, "upload_eval_img.yml"))
def upload_eval_img(uuid):
    # Check uuid is/isnot in app.config["PROJECT_INFO"]
    if not ( uuid in app.config["PROJECT_INFO"].keys()):
        return error_msg(400, {}, "UUID:{} does not exist.".format(uuid), log=True)
    # Check key of front
    if not "iteration" in request.form.keys():
        return error_msg(400, {}, "KEY:iteration does not exist.", log=True)
    # Get project name
    prj_name = app.config["PROJECT_INFO"][uuid]["project_name"]
    # Get value of front
    front_iteration = request.form.get('iteration')
    # Mapping iteration
    dir_iteration = chk.mapping_iteration(uuid, prj_name, front_iteration, front=True)
    if "error" in dir_iteration:
        return error_msg(400, {}, str(dir_iteration[1]), log=True)
    # Save path
    save_path = ROOT + "/" + prj_name + "/" + dir_iteration + "/dataset/eval"
    # Remove folder all file
    shutil.rmtree(save_path)
    # Create new evalaute folder
    os.mkdir(save_path)
    img_list = []
    # Files is multi folder 
    for key in request.files.keys():
        # Get files in files.getlist
        files = request.files.getlist(key)
        # Empty files
        if not files:
            return error_msg(400, {}, "No upload files.", log=True)
        # Get filename in files
        for idx, file in enumerate(files):
            # Most limit 10 pics
            if file and idx < 10:
                # Get file name
                filename = secure_filename(file.filename)
                # Skip other format exclude image format
                if not (filename.split(".")[-1] in ALLOWED_EXTENSIONS["image"]):
                    logging.error("This type of filename is not allowed:[{}:{}]".format(filename, filename.split(".")[-1]))
                    continue
                # Save image
                file.save(os.path.join(save_path, "eval_" + str(idx)+ "." + filename.split(".")[-1]))
                img_path = save_path+"/"+"eval_" + str(idx) + "." + filename.split(".")[-1]
                # Append to list
                if exists(img_path):
                    img_list.append(img_path)
                else:
                    return error_msg(400, {}, "This image does not exist in the Project:[{}:{}]".format(prj_name, img_path), log=True)
            else:
                return error_msg(400, {}, "Upload files are over 10 images-image_name:[{}]".format(file.filename), log=True)
    return success_msg(200, {"eval_img":img_list}, "Success")

@app_eval.route('/<uuid>/evaluate', methods=['POST'])
@swag_from("{}/{}".format(YAML_PATH, "evaluate.yml")) 
def evaluate(uuid):
    eval = Evaluate()
    # Check uuid is/isnot in app.config["PROJECT_INFO"]
    if not ( uuid in app.config["PROJECT_INFO"].keys()):
        return error_msg(400, {}, "UUID:{} does not exist.".format(uuid), log=True)
    # Check key of front
    if not "iteration" in request.get_json().keys():
        return error_msg(400, {}, "KEY:iteration does not exist.", log=True)
    if not "threshold" in request.get_json().keys():
        return error_msg(400, {}, "KEY:threshold does not exist.", log=True)    
    # Get project name
    prj_name = app.config["PROJECT_INFO"][uuid]["project_name"]
    # Get type
    type = app.config["PROJECT_INFO"][uuid]["type"]
    # Get value of front
    front_iteration = request.get_json()['iteration']
    threshold = request.get_json()['threshold']
    # Mapping iteration
    dir_iteration = chk.mapping_iteration(uuid, prj_name, front_iteration, front=True)
    if "error" in dir_iteration:
        return error_msg(400, {}, str(dir_iteration[1]), log=True)
    # Get model.json
    if type == "object_detection":
        model = "yolo"
    elif type == "classification":
        model = type
    # Setting evaluate.json
    msg = eval.set_eval_json(prj_name, dir_iteration, model)
    if msg:
        return error_msg(400, {},  "{}:[{}:{}]".format(msg, prj_name, front_iteration))
    # Evaluate
    command = "python3 evaluate.py -c {}".format(ROOT + '/' +prj_name+'/'+ dir_iteration + '/'+ model + '.json')
    # Run command
    eval.thread_eval(uuid, type, command)
    result = eval.cmd_q.get()
    if "Error" in result.keys():
        return error_msg(400, result, "Out of memory", log=True)
    EVAL_VAL[uuid] = result
    # Threshold
    log_dict = threshold_process(uuid, threshold)
    return success_msg(200, {"detections":log_dict}, "Success")

@app_eval.route('/<uuid>/eval_thresh', methods=['POST'])
@swag_from("{}/{}".format(YAML_PATH, "eval_thresh.yml")) 
def eval_thresh(uuid):
    # Check uuid is/isnot in app.config["PROJECT_INFO"]
    if not ( uuid in app.config["PROJECT_INFO"].keys()):
        return error_msg(400, {}, "UUID:{} does not exist.".format(uuid), log=True)
    if not "threshold" in request.get_json().keys():
        return error_msg(400, {}, "KEY:threshold does not exist.", log=True)  
    threshold = request.get_json()['threshold']
    # Threshold
    log_dict = threshold_process(uuid, threshold)
    return success_msg(200, {"detections":log_dict}, "Success")
    
@app_eval.route('/<uuid>/recheck_bbox', methods=['POST']) 
@swag_from("{}/{}".format(YAML_PATH, "recheck_bbox.yml")) 
def recheck_bbox(uuid):
    # Check uuid is/isnot in app.config["PROJECT_INFO"]
    if not ( uuid in app.config["PROJECT_INFO"].keys()):
        return error_msg(400, {}, "UUID:{} does not exist.".format(uuid), log=True)
    # Check key of front
    if not "iteration" in request.get_json().keys():
        return error_msg(400, {}, "KEY:iteration does not exist.", log=True)
    elif not "image_name" in request.get_json().keys():
        return error_msg(400, {}, "KEY:image_name does not exist.", log=True)
    elif not "box_info" in request.get_json().keys(): 
        return error_msg(400, {}, "KEY:box_info does not exist.", log=True)
    # Get project name
    prj_name = app.config["PROJECT_INFO"][uuid]["project_name"]
    # Get value of front
    front_iteration = request.get_json()['iteration']
    image_name = request.get_json()['image_name']
    box_info = request.get_json()['box_info']
    # Mapping iteration
    dir_iteration = chk.mapping_iteration(uuid, prj_name, front_iteration, front=True)
    if "error" in dir_iteration:
        return error_msg(400, {}, str(dir_iteration[1]), log=True)
    # Move image to dataset
    prj_path = ROOT + '/' + prj_name 
    img_path = prj_path + "/" + dir_iteration + "/dataset/eval/" + image_name
    save_path = prj_path + "/workspace/"
    random_str = ''.join(random.sample(string.ascii_letters + string.digits, 20))
    save_name = os.path.splitext(image_name)[0] + "_" + random_str + os.path.splitext(image_name)[-1]
    if exists(img_path):
        shutil.copyfile(img_path, save_path + "/" + save_name)
        save_bbox(save_path + "/" + save_name, box_info)
        # Append to database 
        updb = Upload_DB(uuid, prj_name, "object_detection", "", save_path, save_name)
        error_db = updb.upload_fillin_ws_info()
        if error_db:
            return error_msg(400, {}, str(error_db[1]))
        return success_msg(200, {}, "Success", 
                            "Save image and boxes in workspace of the Project:[{}-{}:{}]".format(prj_name, save_name, box_info))
    else:
        return error_msg(400, {}, "This image does not exist in iteration of Project:[{}:{}-{}]".format(prj_name, front_iteration, image_name), log=True)

@app_eval.route('/<uuid>/recheck_class', methods=['POST']) 
@swag_from("{}/{}".format(YAML_PATH, "recheck_class.yml")) 
def recheck_class(uuid):
    # Check uuid is/isnot in app.config["PROJECT_INFO"]
    if not ( uuid in app.config["PROJECT_INFO"].keys()):
        return error_msg(400, {}, "UUID:{} does not exist.".format(uuid), log=True)
    # Check key of front
    if not "iteration" in request.get_json().keys():
        return error_msg(400, {}, "KEY:iteration does not exist.", log=True)
    elif not "image_name" in request.get_json().keys():
        return error_msg(400, {}, "KEY:image_name does not exist.", log=True)
    elif not "class_name" in request.get_json().keys():
        return error_msg(400, {}, "KEY:class_name does not exist.", log=True)
    # Get project name
    prj_name = app.config["PROJECT_INFO"][uuid]["project_name"]
    # Get value of front 
    front_iteration = request.get_json()['iteration']
    image_name = request.get_json()['image_name']
    class_name = request.get_json()['class_name']
    # Regular expression
    class_name = regular_expression(class_name)
    # Mapping iteration
    dir_iteration = chk.mapping_iteration(uuid, prj_name, front_iteration, front=True)
    if "error" in dir_iteration:
        return error_msg(400, {}, str(dir_iteration[1]), log=True)
    # Move image to dataset
    prj_path = ROOT + '/' + prj_name 
    img_path = prj_path + "/" + dir_iteration + "/dataset/eval/" + image_name
    main_path = prj_path + "/workspace/"
    random_str = ''.join(random.sample(string.ascii_letters + string.digits, 20))
    save_name = os.path.splitext(image_name)[0] + "_" + random_str + os.path.splitext(image_name)[-1]
    if exists(img_path):
        shutil.copyfile(img_path, main_path + "/" + class_name + "/" + save_name)
        # Append to database 
        updb = Upload_DB(uuid, prj_name, "classification", class_name, main_path, save_name)
        error_db = updb.upload_fillin_ws_info()
        if error_db:
            return error_msg(400, {}, str(error_db[1]))
        return success_msg(200, {}, "Success", "Save image in workspace-label of the Project:[{}-{}:{}]".format(prj_name, save_name, class_name))
    else:
        return error_msg(400, {}, "This image does not exist in iteration of Project:[{}:{}-{}]".format(prj_name, front_iteration, image_name), log=True)
