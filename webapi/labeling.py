from flask import Blueprint, request, jsonify
from flasgger import swag_from
import logging, os, shutil
from webapi import app
from .common.utils import exists, read_json, success_msg, error_msg, write_txt, regular_expression, get_classes_list
from .common.config import ROOT, YAML_MAIN_PATH, COLOR_TABLE_PATH
from .common.labeling_tool import yolo_txt_convert, save_bbox, del_class_txt, add_class_txt, \
                                    del_class_db, cls_change_classes, obj_savebbox_db, rename_cls_class, \
                                    get_all_color_info_db, cls_img_info, obj_img_info
app_labeling = Blueprint( 'labeling', __name__)
# Define API Docs path and Blue Print
YAML_PATH       = YAML_MAIN_PATH + "/labeling"

@app_labeling.route('/<uuid>/add_class', methods=['POST']) 
@swag_from("{}/{}".format(YAML_PATH, "add_class.yml"))
def add_class(uuid):
    # Check uuid is/isnot in app.config["PROJECT_INFO"]
    if not ( uuid in app.config["PROJECT_INFO"].keys()):
        return error_msg(400, {}, "UUID:{} does not exist.".format(uuid), log=True)
    # Check key of front
    if not "class_name" in request.get_json().keys():
        return error_msg(400, {}, "KEY:class_name does not exist.", log=True)
    # Check key of front
    if not "color_id" in request.get_json().keys():
        return error_msg(400, {}, "KEY:color_id does not exist.", log=True)
    # Get project name
    prj_name = app.config["PROJECT_INFO"][uuid]["project_name"] 
    # Get type
    type = app.config["PROJECT_INFO"][uuid]['type']
    # Get value of front
    class_name = request.get_json()['class_name']
    # Regular expression
    class_name = regular_expression(class_name)
    # Get color
    color_id = int(request.get_json()['color_id'])
    # Add to classes.txt
    classes_path = ROOT + '/' + prj_name + "/workspace/classes.txt"
    error_db = add_class_txt(uuid, classes_path, str(class_name), color_id)
    if error_db:
        return error_msg(400, {}, str(error_db[1]))
    # Classification required create class folder
    if type == "classification":
        dir_path = ROOT + '/' + prj_name + "/workspace/" + class_name
        try:
            os.makedirs(dir_path, exist_ok=True, mode=0o777)
        except Exception as exc:
            logging.warn(exc)
            pass

    return success_msg(200, {}, "Success", "Added new class in Project:[{}:{}]".format(prj_name, class_name))

@app_labeling.route('/<uuid>/delete_class', methods=['DELETE']) 
@swag_from("{}/{}".format(YAML_PATH, "delete_class.yml"))
def delete_class(uuid):
    # Check uuid is/isnot in app.config["PROJECT_INFO"]
    if not ( uuid in app.config["PROJECT_INFO"].keys()):
        return error_msg(400, {}, "UUID:{} does not exist.".format(uuid), log=True)
    # Check key of front
    if not "class_name" in request.get_json().keys():
        return error_msg(400, {}, "KEY:class_name does not exist.", log=True) 
    # Get project name
    prj_name = app.config["PROJECT_INFO"][uuid]["project_name"] 
    # Get type
    type = app.config["PROJECT_INFO"][uuid]['type']
    # Get value of front
    class_name = request.get_json()['class_name']
    # Regular expression
    class_name = regular_expression(class_name)  
    # Changed class in classes.txt
    main_path = ROOT + '/' +prj_name + "/workspace"
    origin_cls_db = del_class_txt(uuid, prj_name, type, main_path, class_name)
    if "error" in origin_cls_db:
        return error_msg(400, {}, str(origin_cls_db[1]))
    # Changed class in database
    error_db = del_class_db(uuid, type, prj_name, origin_cls_db, class_name)
    if error_db:
        return error_msg(400, {}, str(error_db[1]))
    # Classification required remove class folder
    if type == "classification":
        dir_path = main_path+"/"+class_name
        if os.path.isdir(dir_path):
            shutil.rmtree(dir_path, ignore_errors=True)
        else:
            return error_msg(400, {}, "This class does not exist in the Project:[{}:{}]".format(prj_name, class_name), log=True) 
    return success_msg(200, {}, "Success", "Delete class in Project:[{}:{}]".format(prj_name, class_name))

@app_labeling.route('/<uuid>/rename_class', methods=['PUT'])
@swag_from("{}/{}".format(YAML_PATH, "rename_class.yml")) 
def rename_class(uuid):
    # Check uuid is/isnot in app.config["PROJECT_INFO"]
    if not ( uuid in app.config["PROJECT_INFO"].keys()):
        return error_msg(400, {}, "UUID:{} does not exist.".format(uuid), log=True)
    # Check key of front
    if not "class_name" in request.get_json().keys():
        return error_msg(400, {}, "KEY:class_name does not exist.", log=True)
    elif not "new_name" in request.get_json().keys():
        return error_msg(400, {}, "KEY:new_name does not exist.", log=True)
    # Get project name
    prj_name = app.config["PROJECT_INFO"][uuid]["project_name"] 
    # Get type
    type = app.config["PROJECT_INFO"][uuid]['type']
    # Get value of front
    class_name = request.get_json()['class_name']
    new_name = request.get_json()['new_name']
    # Regular expression
    class_name = regular_expression(class_name) 
    new_name = regular_expression(new_name)
    # Rename class in classes.txt
    classes_path = ROOT + '/' + prj_name + "/workspace/classes.txt"
    if exists(classes_path):
        # Read orignal file
        class_text = get_classes_list(classes_path)
        # Change class string
        if class_name in class_text:
            idx = class_text.index(class_name)
            class_text[idx] = new_name
        else:
            return error_msg(400, {}, "This class does not exist in classes.txt of the Project:[{}:{}]".format(prj_name, class_name), log=True)
        # Remove orignal file
        os.remove(classes_path)
        # Writing classes.txt
        for cls in class_text:
            write_txt(classes_path, cls)
    else:
        return error_msg(400, {}, "This classes.txt does not exist in the Project:[{}]".format(classes_path))
    # Classification required rename class folder
    if type == "classification":
        dir_path = ROOT + '/' + prj_name + "/workspace/" + class_name
        new_path = ROOT + '/' + prj_name + "/workspace/" + new_name
        if os.path.isdir(dir_path):
            os.rename(dir_path, new_path)
        else:
            return error_msg(400, {}, "This class does not exist in Project:[{}:{}]".format(prj_name, class_name), log=True) 
        # Renamed database img_path
        error_db = rename_cls_class(uuid, prj_name, class_name, new_name)
        if error_db:
            return error_msg(400, {}, str(error_db[1]))
    return success_msg(200, {}, "Success", "Renamed class in Project:[{}:{} -> {}]".format(prj_name, class_name, new_name))

@app_labeling.route('/<uuid>/edit_img_class', methods=['POST']) 
@swag_from("{}/{}".format(YAML_PATH, "edit_img_class.yml")) 
def edit_img_class(uuid):
    # Check uuid is/isnot in app.config["PROJECT_INFO"]
    if not ( uuid in app.config["PROJECT_INFO"].keys()):
        return error_msg(400, {}, "UUID:{} does not exist.".format(uuid), log=True)
    # Check key of front
    if not "images_info" in request.get_json().keys():
        return error_msg(400, {}, "KEY:images_info does not exist.", log=True)
    elif not "class_name" in request.get_json().keys():
        return error_msg(400, {}, "KEY:class_name does not exist.", log=True)
    # Get project name
    prj_name = app.config["PROJECT_INFO"][uuid]["project_name"]
    # Get type
    type = app.config["PROJECT_INFO"][uuid]["type"]
    if type != "classification":
        return error_msg(400, {}, "Type is not \'Classification\':[{}]".format(type), log=True)
    # Get value of front 
    images_info = request.get_json()['images_info']
    class_name = request.get_json()['class_name'] 
    # Regular expression
    class_name = regular_expression(class_name)          
    # class_name == "Unlabeled"
    if class_name== "Unlabeled":
        class_name = ""
    # If the folder does not exist, then create a new folder and append a new class in classes.txt
    dir_path = ROOT + '/' + prj_name + "/workspace/" + class_name
    if not os.path.isdir(dir_path):
        logging.warn("Create new folder in the Project:[{}:{}]".format(prj_name, class_name))
        os.makedirs(dir_path, exist_ok=True, mode=0o777)
        # Append a new class in classes.txt
        classes_path = ROOT + '/' + prj_name + "/workspace/classes.txt"
        if exists(classes_path):
            classes_list = get_classes_list(classes_path)
            if not (class_name in classes_list):
                write_txt(classes_path, class_name)
        else:
            return error_msg(400, {}, "This classes.txt does not exist in the Project:[{}]".format(classes_path), log=True)                
    # Move file and chagned database
    error_db = cls_change_classes(uuid, prj_name, class_name, images_info)
    if error_db:
        return error_msg(400, {}, str(error_db[1]))
    return success_msg(200, {}, "Success", "Change images class in the Project:[{}:{} -> {}]".format(prj_name, images_info, class_name))

@app_labeling.route('/<uuid>/get_bbox', methods=['POST']) 
@swag_from("{}/{}".format(YAML_PATH, "get_bbox.yml")) 
def get_bbox(uuid):
    # Check uuid is/isnot in app.config["PROJECT_INFO"]
    if not ( uuid in app.config["PROJECT_INFO"].keys()):
        return error_msg(400, {}, "UUID:{} does not exist.".format(uuid), log=True)
    # Check key of front
    if not "image_path" in request.get_json().keys():
        return error_msg(400, {}, "KEY:image_path does not exist.", log=True)
    # Get project name
    prj_name = app.config["PROJECT_INFO"][uuid]["project_name"]
    # Get value of front 
    image_path = request.get_json()['image_path']
    img_path = "." + image_path
    if exists(img_path):
        bbox_info = yolo_txt_convert(uuid, img_path)
        if "error" in bbox_info:
            return error_msg(400, {}, bbox_info[1], log=True)
        img_shape, box = bbox_info
        return success_msg(200, {"img_shape":img_shape, "box_info":box}, "Success", 
                                    "Get info of bbox:{}".format({"filename":os.path.split(image_path)[-1], "box_info":box, "img_shape":img_shape}))
    else:
        return error_msg(400, {}, "This image does not exist in the Project:[{}:{}]".format(prj_name, img_path), log=True)

@app_labeling.route('/<uuid>/update_bbox', methods=['POST']) 
@swag_from("{}/{}".format(YAML_PATH, "update_bbox.yml")) 
def update_bbox(uuid):
    # Check uuid is/isnot in app.config["PROJECT_INFO"]
    if not ( uuid in app.config["PROJECT_INFO"].keys()):
        return error_msg(400, {}, "UUID:{} does not exist.".format(uuid), log=True)
    # Check key of front
    if not "image_name" in request.get_json().keys():
        return error_msg(400, {}, "KEY:image_name does not exist.", log=True)
    elif not "box_info" in request.get_json().keys(): 
        return error_msg(400, {}, "KEY:box_info does not exist.", log=True)
    # Get project name
    prj_name = app.config["PROJECT_INFO"][uuid]["project_name"]
    # Get value of front
    image_name = request.get_json()['image_name']
    box_info = request.get_json()['box_info']
    # Save new bbox
    img_path = ROOT + '/' + prj_name + "/workspace/" + image_name
    if exists(img_path):
        # Save in txt
        cls_idx = save_bbox(img_path, box_info)
        # Save in db
        error_db = obj_savebbox_db(image_name, cls_idx, uuid)
        if error_db:
            return error_msg(400, {}, str(error_db[1]))
        return success_msg(200, {}, "Success", "Update box in image of Project:[{}:{}:{}]".format(prj_name, image_name, box_info))
    else:
        return error_msg(400, {}, "This image does not exist in Project:[{}:{}]".format(prj_name, image_name), log=True)

@app_labeling.route('/get_img_cls_nums/<uuid>/<path:path>', methods=['GET'])
@swag_from("{}/{}".format(YAML_PATH, "get_img_cls_nums.yml")) 
def get_img_cls_nums(uuid, path):
    # Check uuid is/isnot in app.config["PROJECT_INFO"]
    if not ( uuid in app.config["PROJECT_INFO"].keys()):
        return error_msg(400, {}, "UUID:{} does not exist.".format(uuid), log=True)
    # Get type
    type = app.config["PROJECT_INFO"][uuid]['type']
    # Get project name
    prj_name = app.config["PROJECT_INFO"][uuid]["project_name"]
    # Get color infomation in color_id of the database
    color_info_db = get_all_color_info_db(uuid, path)
    # Prevent error 
    if "error" in color_info_db:
        return error_msg(400, {}, str(color_info_db[1]))
    # combination path
    img_path = "./" + path
    # Return class and num
    if exists(img_path):
        if type == "classification":
            img_info = cls_img_info(prj_name, img_path, color_info_db)
            # Prevent error 
            if "error" in img_info:
                return error_msg(400, {}, str(img_info[1]), log=True)
            return success_msg(200, img_info, "Success", "Get infomation of image classes:[{}:{}]".format(path, img_info))
        elif type == "object_detection":
            img_info = obj_img_info(uuid, img_path, color_info_db)
            # Prevent error 
            if "error" in img_info:
                return error_msg(400, {}, str(img_info[1]), log=True)
            return success_msg(200, img_info, "Success", "Get infomation of image classes:[{}:{}]".format(path, img_info))
    else:
        return error_msg(400, {}, "This image does not exist in Project:[{}:{}]".format(prj_name, path), log=True)

@app_labeling.route('/get_color_table',methods=['GET'])
@swag_from("{}/{}".format(YAML_PATH, "get_color_table.yml")) 
def get_color_table():
    color_table = read_json(COLOR_TABLE_PATH)
    return success_msg(200, color_table, "Success")