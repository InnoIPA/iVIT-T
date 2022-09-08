from flask import Blueprint, request, jsonify
from flasgger import swag_from
import logging
import os, shutil
from pathlib import Path
from webapi import app
from .common.utils import exists, read_json, read_txt, success_msg, error_msg, write_txt
from .common.labeling_tool import yolo_txt_convert, save_bbox

app_labeling = Blueprint( 'labeling', __name__)

@app_labeling.route('/<uuid>/add_class', methods=['POST']) 
@swag_from('./descript/labeling/add_class.yml')
def add_class(uuid):
    if request.method == 'POST':
        # Check uuid is/isnot in app.config["PROJECT_INFO"]
        if not ( uuid in app.config["PROJECT_INFO"].keys()):
            return error_msg("UUID:{} is not exist.".format(uuid))
        # Check key of front
        if not "class_name" in request.get_json().keys():
            return error_msg("KEY:class_name is not exist.")
        # Get project name
        prj_name = app.config["PROJECT_INFO"][uuid]["front_project"]["project_name"] 
        # Get type
        type = app.config["PROJECT_INFO"][uuid]["front_project"]['type']
        # Get value of front
        class_name = request.get_json()['class_name']

        # classification required create class folder
        if type == "classification":
            dir_path = "./Project/"+prj_name+"/workspace/"+class_name
            try:
                os.makedirs(dir_path, exist_ok=True, mode=0o777)
            except Exception as exc:
                logging.warn(exc)
                pass

        # Add to classes.txt
        classes_path = "./Project/"+prj_name+"/workspace/classes.txt"
        write_txt(classes_path, class_name)
            
        return success_msg("Added new class:{} in Project:{}".format(class_name, prj_name))

@app_labeling.route('/<uuid>/delete_class', methods=['POST']) 
@swag_from('./descript/labeling/delete_class.yml')
def delete_class(uuid):
    if request.method == 'POST':
        # Check uuid is/isnot in app.config["PROJECT_INFO"]
        if not ( uuid in app.config["PROJECT_INFO"].keys()):
            return error_msg("UUID:{} is not exist.".format(uuid))
        # Check key of front
        if not "class_name" in request.get_json().keys():
            return error_msg("KEY:class_name is not exist.")
        # Get project name
        prj_name = app.config["PROJECT_INFO"][uuid]["front_project"]["project_name"] 
        # Get type
        type = app.config["PROJECT_INFO"][uuid]["front_project"]['type']
        # Get value of front
        class_name = request.get_json()['class_name']

        # classification required remove class folder
        if type == "classification":
            dir_path = "./Project/"+prj_name+"/workspace/"+class_name
            if os.path.isdir(dir_path):
                shutil.rmtree(dir_path, ignore_errors=True)

        # Add to classes.txt
        classes_path = "./Project/"+prj_name+"/workspace/classes.txt"
        if exists(classes_path):
            # Read orignal file
            class_text = [cls for cls in read_txt(classes_path).split("\n") if cls !=""]
            # Remove orignal file
            os.remove(classes_path)
            # Remove class string
            if class_name in class_text:
                class_text.remove(class_name)
            else:
                logging.error("This class:{} is not exist in classes.txt of Project:{}".format(class_name, prj_name))
            # Writing classes.txt
            for cls in class_text:
                write_txt(classes_path, cls)

        return success_msg("Delete class:{} in Project:{}".format(class_name, prj_name))

@app_labeling.route('/<uuid>/rename_class', methods=['POST']) 
@swag_from('./descript/labeling/rename_class.yml')
def rename_class(uuid):
    if request.method == 'POST':
        # Check uuid is/isnot in app.config["PROJECT_INFO"]
        if not ( uuid in app.config["PROJECT_INFO"].keys()):
            return error_msg("UUID:{} is not exist.".format(uuid))
        # Check key of front
        if not "class_name" in request.get_json().keys():
            return error_msg("KEY:class_name is not exist.")
        elif not "new_name" in request.get_json().keys():
            return error_msg("KEY:new_name is not exist.")
        # Get project name
        prj_name = app.config["PROJECT_INFO"][uuid]["front_project"]["project_name"] 
        # Get type
        type = app.config["PROJECT_INFO"][uuid]["front_project"]['type']
        # Get value of front
        class_name = request.get_json()['class_name']
        new_name = request.get_json()['new_name']

        # classification required rename class folder
        if type == "classification":
            dir_path = "./Project/"+prj_name+"/workspace/"+class_name
            new_path = "./Project/"+prj_name+"/workspace/"+new_name
            if os.path.isdir(dir_path):
                os.rename(dir_path, new_path)

        # rename class in classes.txt
        classes_path = "./Project/"+prj_name+"/workspace/classes.txt"
        if exists(classes_path):
            # Read orignal file
            class_text = [cls for cls in read_txt(classes_path).split("\n") if cls !=""]
            # Remove orignal file
            os.remove(classes_path)
            # Change class string
            if class_name in class_text:
                idx = class_text.index(class_name)
                class_text[idx] = new_name
            else:
                logging.error("This class:{} is not exist in classes.txt of Project:{}".format(class_name, prj_name))
            # Writing classes.txt
            for cls in class_text:
                write_txt(classes_path, cls)

        return success_msg("Renamed class:{} to {} in Project:{}".format(class_name, new_name, prj_name))

@app_labeling.route('/<uuid>/edit_img_class', methods=['POST']) 
@swag_from('./descript/labeling/edit_img_class.yml')
def edit_img_class(uuid):
    if request.method == 'POST':
        # Check uuid is/isnot in app.config["PROJECT_INFO"]
        if not ( uuid in app.config["PROJECT_INFO"].keys()):
            return error_msg("UUID:{} is not exist.".format(uuid))
        # Check key of front
        if not "images_info" in request.get_json().keys():
            return error_msg("KEY:images_info is not exist.")
        elif not "class_name" in request.get_json().keys():
            return error_msg("KEY:class_name is not exist.")
        # Get project name
        prj_name = app.config["PROJECT_INFO"][uuid]["front_project"]["project_name"]
        # Get value of front 
        images_info = request.get_json()['images_info']
        class_name = request.get_json()['class_name'] 
        
        # class_name== "Unlabeled"
        if class_name== "Unlabeled":
            class_name = ""

        # If target dir is not exist then create target Directory
        dir_path = "./Project/"+prj_name+"/workspace/"+class_name
        if not os.path.isdir(dir_path):
            os.makedirs(dir_path, exist_ok=True, mode=0o777)
            # Add to classes.txt
            classes_path = "./Project/"+prj_name+"/workspace/classes.txt"
            if exists(classes_path):
                write_txt(classes_path, class_name)

        # Change file in other dir
        for key in images_info.keys():
            if key == "Unlabeled":
                label = ""
            else:
                label = key
                
            if os.path.isdir("./Project/"+prj_name+"/workspace/"+label):
                for value in images_info[key]:
                    shutil.move("./Project/"+prj_name+"/workspace/"+label+'/'+value, "./Project/"+prj_name+"/workspace/"+class_name+'/'+value)

        return success_msg("Change images:{} to {} in Project:{}".format(images_info, class_name, prj_name))

@app_labeling.route('/<uuid>/get_bbox', methods=['POST']) 
@swag_from('./descript/labeling/get_bbox.yml')
def get_bbox(uuid):
    if request.method == 'POST':
        # Check uuid is/isnot in app.config["PROJECT_INFO"]
        if not ( uuid in app.config["PROJECT_INFO"].keys()):
            return error_msg("UUID:{} is not exist.".format(uuid))
        # Check key of front
        if not "image_path" in request.get_json().keys():
            return error_msg("KEY:image_path is not exist.")
        # Get project name
        prj_name = app.config["PROJECT_INFO"][uuid]["front_project"]["project_name"]
        # Get value of front 
        image_path = request.get_json()['image_path']

        img_path = "."+ image_path
        if exists(img_path):
            img_shape, box_info = yolo_txt_convert(img_path)
            logging.info({"img_shape":img_shape, "box_info":box_info})
            return jsonify({"img_shape":img_shape, "box_info":box_info})
        else:
            logging.error("This image:{} is not exist in Project:{}".format(img_path, prj_name))
            return error_msg("This image:{} is not exist in Project:{}".format(img_path, prj_name))

@app_labeling.route('/<uuid>/update_bbox', methods=['POST']) 
@swag_from('./descript/labeling/update_bbox.yml')
def update_bbox(uuid):
    if request.method == 'POST':
        # Check uuid is/isnot in app.config["PROJECT_INFO"]
        if not ( uuid in app.config["PROJECT_INFO"].keys()):
            return error_msg("UUID:{} is not exist.".format(uuid))
        # Check key of front
        if not "image_name" in request.get_json().keys():
            return error_msg("KEY:image_name is not exist.")
        elif not "box_info" in request.get_json().keys(): 
            return error_msg("KEY:box_info is not exist.")
        # Get project name
        prj_name = app.config["PROJECT_INFO"][uuid]["front_project"]["project_name"]
        # Get value of front
        image_name = request.get_json()['image_name']
        box_info = request.get_json()['box_info']

        img_path = "./Project/"+prj_name+"/workspace/"+image_name
        if exists(img_path):
            save_bbox(img_path, box_info)
            return success_msg("Update box:{} in image:{} of Project:{}".format(box_info, image_name, prj_name))
        else:
            return error_msg("This image:{} is not exist in Project:{}".format(image_name, prj_name))

@app_labeling.route('/get_img_cls/<type>/<path:path>', methods=['GET'])
@swag_from('./descript/labeling/get_img_cls.yml')
def get_img_cls(type, path):
    # combination path
    img_path = "./"+ path
    # Return class and num
    if exists(img_path):
        if type == "classification":
            class_name = path.split("/")[-2]
            if "workspace" == class_name:
                class_name = "Unlabeled"
            return jsonify({class_name:1})
        elif type == "object_detection":
            class_info = {}
            _, box_info = yolo_txt_convert(img_path)
            if len(box_info)==0:
                return jsonify({"Unlabeled":0})

            # Appnd to class_info
            for idx in box_info:
                if idx["class_name"] in class_info.keys():
                    class_info[idx["class_name"]] = class_info[idx["class_name"]]+1
                else:
                    class_info[idx["class_name"]] = 1
            
            return jsonify(class_info)
            
    else:
        return error_msg("This image is not exist:{}".format(img_path))

@app_labeling.route('/get_color_bar',methods=['GET'])
@swag_from('./descript/labeling/get_color_bar.yml')
def get_color_bar():
    color_path = "./webapi/common/color_bar.json"
    color_bar = read_json(color_path)
    return jsonify(color_bar)