from flask import Blueprint, request, jsonify
from flasgger import swag_from
import logging, os, shutil
from webapi import app
from .common.utils import exists, read_json, read_txt, success_msg, error_msg, write_txt, regular_expression
from .common.config import ROOT, YAML_MAIN_PATH
from .common.labeling_tool import yolo_txt_convert, save_bbox, del_cls_txt, add_cls_txt, del_cls_db, cls_change_class, obj_savebbox_db
app_labeling = Blueprint( 'labeling', __name__)
# Define API Docs path and Blue Print
YAML_PATH       = YAML_MAIN_PATH + "/labeling"

@app_labeling.route('/<uuid>/add_class', methods=['POST']) 
@swag_from("{}/{}".format(YAML_PATH, "add_class.yml"))
def add_class(uuid):
    if request.method == 'POST':
        # Check uuid is/isnot in app.config["PROJECT_INFO"]
        if not ( uuid in app.config["PROJECT_INFO"].keys()):
            return error_msg("UUID:{} does not exist.".format(uuid))
        # Check key of front
        if not "class_name" in request.get_json().keys():
            return error_msg("KEY:class_name does not exist.")
        # Get project name
        prj_name = app.config["PROJECT_INFO"][uuid]["project_name"] 
        # Get type
        type = app.config["PROJECT_INFO"][uuid]['type']
        # Get value of front
        class_name = request.get_json()['class_name']
        # Regular expression
        class_name = regular_expression(class_name)
        # classification required create class folder
        if type == "classification":
            dir_path = ROOT + '/' + prj_name + "/workspace/" + class_name
            try:
                os.makedirs(dir_path, exist_ok=True, mode=0o777)
            except Exception as exc:
                logging.warn(exc)
                pass
        # Add to classes.txt
        classes_path = ROOT + '/' + prj_name + "/workspace/classes.txt"
        add_cls_txt(class_name, classes_path)
            
        return success_msg("Added new class:[{}] in Project:[{}]".format(class_name, prj_name))

@app_labeling.route('/<uuid>/delete_class', methods=['DELETE']) 
@swag_from("{}/{}".format(YAML_PATH, "delete_class.yml"))
def delete_class(uuid):
    if request.method == 'DELETE':
        # Check uuid is/isnot in app.config["PROJECT_INFO"]
        if not ( uuid in app.config["PROJECT_INFO"].keys()):
            return error_msg("UUID:{} does not exist.".format(uuid))
        # Check key of front
        if not "class_name" in request.get_json().keys():
            return error_msg("KEY:class_name does not exist.")
        # Get project name
        prj_name = app.config["PROJECT_INFO"][uuid]["project_name"] 
        # Get type
        type = app.config["PROJECT_INFO"][uuid]['type']
        # Get value of front
        class_name = request.get_json()['class_name']
        # Regular expression
        class_name = regular_expression(class_name)  
        # classification required remove class folder
        main_path = ROOT + '/' +prj_name + "/workspace"
        if type == "classification":
            dir_path = main_path+"/"+class_name
            if os.path.isdir(dir_path):
                shutil.rmtree(dir_path, ignore_errors=True)
            else:
                return error_msg("This class:[{}] does not exist in project:[{}]".format(class_name, prj_name)) 
        # Changed class in classes.txt
        classes_path = main_path+"/classes.txt"
        orignal_cls = []
        orignal_cls = del_cls_txt(class_name, classes_path, main_path, prj_name, orignal_cls, type)
        if "error" in orignal_cls:
            return error_msg(str(orignal_cls[1]))
        # Changed class in database
        info = del_cls_db(class_name, uuid, orignal_cls, type)
        if info is not None:
            return error_msg(str(info[1]))

        return success_msg("Delete class:{} in Project:{}".format(class_name, prj_name))

@app_labeling.route('/<uuid>/rename_class', methods=['PUT'])
@swag_from("{}/{}".format(YAML_PATH, "rename_class.yml")) 
def rename_class(uuid):
    if request.method == 'PUT':
        # Check uuid is/isnot in app.config["PROJECT_INFO"]
        if not ( uuid in app.config["PROJECT_INFO"].keys()):
            return error_msg("UUID:{} does not exist.".format(uuid))
        # Check key of front
        if not "class_name" in request.get_json().keys():
            return error_msg("KEY:class_name does not exist.")
        elif not "new_name" in request.get_json().keys():
            return error_msg("KEY:new_name does not exist.")
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
        # Classification required rename class folder
        if type == "classification":
            dir_path = ROOT + '/' +prj_name+"/workspace/"+class_name
            new_path = ROOT + '/' +prj_name+"/workspace/"+new_name
            if os.path.isdir(dir_path):
                os.rename(dir_path, new_path)
            else:
                return error_msg("This class:[{}] does not exist in project:[{}]".format(class_name, prj_name)) 
        # Rename class in classes.txt
        classes_path = ROOT + '/' +prj_name+"/workspace/classes.txt"
        if exists(classes_path):
            # Read orignal file
            class_text = [cls for cls in read_txt(classes_path).split("\n") if cls !=""]
            # Change class string
            if class_name in class_text:
                idx = class_text.index(class_name)
                class_text[idx] = new_name
            else:
                return error_msg("This class:[{}] does not exist in classes.txt of Project:[{}]".format(class_name, prj_name))
            # Remove orignal file
            os.remove(classes_path)
            # Writing classes.txt
            for cls in class_text:
                write_txt(classes_path, cls)
        else:
            return error_msg("This classes.txt does not exist.")
        return success_msg("Renamed class:{} to {} in Project:{}".format(class_name, new_name, prj_name))

@app_labeling.route('/<uuid>/edit_img_class', methods=['POST']) 
@swag_from("{}/{}".format(YAML_PATH, "edit_img_class.yml")) 
def edit_img_class(uuid):
    if request.method == 'POST':
        # Check uuid is/isnot in app.config["PROJECT_INFO"]
        if not ( uuid in app.config["PROJECT_INFO"].keys()):
            return error_msg("UUID:{} does not exist.".format(uuid))
        # Check key of front
        if not "images_info" in request.get_json().keys():
            return error_msg("KEY:images_info does not exist.")
        elif not "class_name" in request.get_json().keys():
            return error_msg("KEY:class_name does not exist.")
        # Get project name
        prj_name = app.config["PROJECT_INFO"][uuid]["project_name"]
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
            logging.warn("Create new folder:[{}] in Project:[{}]".format(class_name, prj_name))
            os.makedirs(dir_path, exist_ok=True, mode=0o777)
            # Append a new class in classes.txt
            classes_path = ROOT + '/' +prj_name+"/workspace/classes.txt"
            if exists(classes_path):
                write_txt(classes_path, class_name)
            else:
                return error_msg("This classes.txt does not exist.")                
        # Move file and chagned database
        info = cls_change_class(images_info, prj_name, class_name, uuid)
        if info is not None:
            return error_msg(str(info[1]))
        return success_msg("Change images:{} to [{}] in Project:[{}]".format(images_info, class_name, prj_name))

@app_labeling.route('/<uuid>/get_bbox', methods=['POST']) 
@swag_from("{}/{}".format(YAML_PATH, "get_bbox.yml")) 
def get_bbox(uuid):
    if request.method == 'POST':
        # Check uuid is/isnot in app.config["PROJECT_INFO"]
        if not ( uuid in app.config["PROJECT_INFO"].keys()):
            return error_msg("UUID:{} does not exist.".format(uuid))
        # Check key of front
        if not "image_path" in request.get_json().keys():
            return error_msg("KEY:image_path does not exist.")
        # Get project name
        prj_name = app.config["PROJECT_INFO"][uuid]["project_name"]
        # Get value of front 
        image_path = request.get_json()['image_path']
        img_path = "."+ image_path
        if exists(img_path):
            img_shape, box_info = yolo_txt_convert(img_path)
            logging.info("Get info of bbox:{}".format({"filename":os.path.split(image_path)[-1], "box_info":box_info, "img_shape":img_shape}))
            return jsonify({"img_shape":img_shape, "box_info":box_info})
        else:
            return error_msg("This image:[{}] does not exist in Project:[{}]".format(img_path, prj_name))

@app_labeling.route('/<uuid>/update_bbox', methods=['POST']) 
@swag_from("{}/{}".format(YAML_PATH, "update_bbox.yml")) 
def update_bbox(uuid):
    if request.method == 'POST':
        # Check uuid is/isnot in app.config["PROJECT_INFO"]
        if not ( uuid in app.config["PROJECT_INFO"].keys()):
            return error_msg("UUID:{} does not exist.".format(uuid))
        # Check key of front
        if not "image_name" in request.get_json().keys():
            return error_msg("KEY:image_name does not exist.")
        elif not "box_info" in request.get_json().keys(): 
            return error_msg("KEY:box_info does not exist.")
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
            if "error" in cls_idx:
                return error_msg(str(cls_idx[1]))
            # Save in db
            info_db = obj_savebbox_db(image_name, cls_idx, uuid)
            if info_db is not None:
                return error_msg(str(info_db[1]))
            return success_msg("Update box:{} in image:[{}] of Project:[{}]".format(box_info, image_name, prj_name))
        else:
            return error_msg("This image:[{}] does not exist in Project:[{}]".format(image_name, prj_name))

@app_labeling.route('/get_img_cls_nums/<type>/<path:path>', methods=['GET'])
@swag_from("{}/{}".format(YAML_PATH, "get_img_cls_nums.yml")) 
def get_img_cls_nums(type, path):
    # combination path
    img_path = "./"+ path
    # Return class and num
    if exists(img_path):
        if type == "classification":
            class_name = path.split("/")[-2]
            if "workspace" == class_name or "" == class_name:
                class_name = "Unlabeled"
            logging.info("Get class numbers of image:[{}:{}]".format(os.path.split(path)[-1], {class_name:1}))
            return jsonify({class_name:1})

        elif type == "object_detection":
            class_info = {}
            _, box_info = yolo_txt_convert(img_path)
            if len(box_info)==0:
                logging.info("Get class numbers of image:[{}:{}]".format(os.path.split(path)[-1], {"Unlabeled":0}))
                return jsonify({"Unlabeled":0})
            # Appnd to class_info
            for idx in box_info:
                if idx["class_name"] in class_info.keys():
                    class_info[idx["class_name"]] = class_info[idx["class_name"]]+1
                else:
                    class_info[idx["class_name"]] = 1
            logging.info("Get class numbers of image:[{}:{}]".format(os.path.split(path)[-1], class_info))
            return jsonify(class_info)
    else:
        return error_msg("This image does not exist:{}".format(img_path))

@app_labeling.route('/get_color_bar',methods=['GET'])
@swag_from("{}/{}".format(YAML_PATH, "get_color_bar.yml")) 
def get_color_bar():
    color_path = "./webapi/common/color_bar.json"
    color_bar = read_json(color_path)
    return jsonify(color_bar)