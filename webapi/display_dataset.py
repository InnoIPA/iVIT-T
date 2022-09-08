from flask import Blueprint, request, jsonify, send_from_directory
from flasgger import swag_from
import logging
import os
from pathlib import Path
from natsort import natsorted
from webapi import app
from .common.utils import success_msg, error_msg, exists
from .common.display_tool import get_folder_image, get_obj_classes_img, count_dataset

app_dy_dt = Blueprint( 'display_dataset', __name__)

@app_dy_dt.route('/<uuid>/get_dataset', methods=['GET']) 
@swag_from('./descript/display_dataset/get_dataset.yml')
def get_dataset(uuid):
    # Check uuid is/isnot in app.config["PROJECT_INFO"]
    if not ( uuid in app.config["PROJECT_INFO"].keys()):
        return error_msg("UUID:{} is not exist.".format(uuid))
    # Get project name
    prj_name = app.config["PROJECT_INFO"][uuid]["front_project"]["project_name"]   

    prj_path = "./Project/"+prj_name
    folder_name = [ dir for dir in natsorted(os.listdir(prj_path)) if os.path.isdir(prj_path+"/"+dir)]
    return jsonify({"folder_name":folder_name}) 

@app_dy_dt.route('/<uuid>/filter_dataset', methods=['POST']) 
@swag_from('./descript/display_dataset/filter_dataset.yml')
def filter_dataset(uuid):
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

        # Give img path
        iter_path = "./Project/"+prj_name+"/"+iteration
        if "workspace" == iteration:
            return jsonify({"img_path":get_folder_image(iter_path)})
        else:
            # train/val/test in iteration/dataset except eval
            iter_path = iter_path+"/dataset"
            img_list = []
            folder_list = [iter_path+"/"+name for name in natsorted(os.listdir(iter_path)) if os.path.isdir(iter_path+"/"+name) and name !="eval"]
            for dir in folder_list:
                img_list.extend(get_folder_image(dir))
            return jsonify({"img_path":img_list})

@app_dy_dt.route('/display_img/<path:path>', methods=['GET'])
@swag_from('./descript/display_dataset/display_img.yml')
def display_img(path):
    path_list= path.split("/")
    path = str(Path(__file__).resolve().parents[1]/"")
    # combination path
    for num, string in enumerate(path_list):
        if num != len(path_list)-1:
            path = path+"/"+string

    if exists(path+"/"+path_list[-1]):
        return send_from_directory(path, path_list[-1])
    else:
        return error_msg("This image is not exist:{}".format(path+"/"+path_list[-1]))

@app_dy_dt.route('/<uuid>/filter_classes', methods=['POST']) 
@swag_from('./descript/display_dataset/filter_classes.yml')
def filter_classes(uuid):
    if request.method == 'POST':
        # Check uuid is/isnot in app.config["PROJECT_INFO"]
        if not ( uuid in app.config["PROJECT_INFO"].keys()):
            return error_msg("UUID:{} is not exist.".format(uuid))
        # Check key of front
        if not "iteration" in request.get_json().keys():
            return error_msg("KEY:iteration is not exist.")
        elif not "class_name" in request.get_json().keys():
            return error_msg("KEY:class_name is not exist.")
        # Get project name
        prj_name = app.config["PROJECT_INFO"][uuid]["front_project"]["project_name"] 
        # Get type
        type = app.config["PROJECT_INFO"][uuid]["front_project"]['type']
        # Get value of front
        iteration = request.get_json()['iteration']
        class_name = request.get_json()['class_name']

        # class_name== "Unlabeled"
        if class_name== "Unlabeled":
            class_name = ""

        # Give img path
        iter_path = "./Project/"+prj_name+"/"+iteration
        if type == "classification":
            iter_cls_path = iter_path+"/"+class_name
            if "workspace" == iteration:
                img_list = get_folder_image(iter_cls_path, filetype=False)
                return jsonify({"img_path":img_list, "length":len(img_list)})
            else:
                # train/val/test in iteration/dataset except eval
                iter_path = iter_path+"/dataset"
                img_list = []
                folder_list = [iter_path+"/"+name for name in natsorted(os.listdir(iter_path)) if os.path.isdir(iter_path+"/"+name) and name !="eval"]
                for dir in folder_list:
                    dir = dir + "/" + class_name
                    img_list.extend(get_folder_image(dir, filetype=False))
                return jsonify({"img_path":img_list, "length":len(img_list)})

        elif type == "object_detection":
            if "workspace" == iteration:
                classes_path = iter_path+ '/'+"classes.txt"
                img_list = get_obj_classes_img(iter_path, class_name, classes_path)
                return jsonify({"img_path":img_list, "length":len(img_list)})
            else:
                # train/val/test in iteration/dataset except eval
                iter_path = iter_path+"/dataset"
                img_list = []
                folder_list = [iter_path+"/"+name for name in natsorted(os.listdir(iter_path)) if os.path.isdir(iter_path+"/"+name) and name !="eval"]
                classes_path = iter_path+ '/'+"classes.txt"
                for dir in folder_list:
                    img_list.extend(get_obj_classes_img(dir, class_name, classes_path))
                return jsonify({"img_path":img_list, "length":len(img_list)})            

@app_dy_dt.route('/<uuid>/delete_img', methods=['POST']) 
@swag_from('./descript/display_dataset/delete_img.yml')
def delete_img(uuid):
    if request.method == 'POST':
        # Check uuid is/isnot in app.config["PROJECT_INFO"]
        if not ( uuid in app.config["PROJECT_INFO"].keys()):
            return error_msg("UUID:{} is not exist.".format(uuid))
        # Check key of front
        if not "image_info" in request.get_json().keys():
            return error_msg("KEY:image_info is not exist.")
        # Get project name
        prj_name = app.config["PROJECT_INFO"][uuid]["front_project"]["project_name"] 
        # Get type
        type = app.config["PROJECT_INFO"][uuid]["front_project"]['type']
        # Get value of front
        image_info_list = request.get_json()['image_info']
        
        for key in image_info_list.keys(): 
            if key == "Unlabeled":
                label = ""
            else:
                label = key

            if os.path.isdir("./Project/"+prj_name+"/workspace"+'/'+label):
                for name in image_info_list[key]:
                    logging.info("Removed:{}".format("./Project/"+prj_name+"/workspace"+'/'+label+'/'+name))
                    os.remove("./Project/"+prj_name+"/workspace"+'/'+label+'/'+name)
                    # if object_detection need to remove txt
                    if type == 'object_detection' and os.path.isfile("./Project/"+prj_name+"/workspace"+'/'+label+'/'+name.split('.')[0]+'.txt'):
                        logging.info("Removed:{}".format("./Project/"+prj_name+"/workspace"+'/'+label+'/'+name.split('.')[0]+'.txt'))
                        os.remove("./Project/"+prj_name+"/workspace"+'/'+label+'/'+name.split('.')[0]+'.txt')

        return success_msg("Delete images- project:{}, images:{}".format(prj_name, image_info_list))

@app_dy_dt.route('/<uuid>/iter_cls_num', methods=['POST']) 
@swag_from('./descript/display_dataset/iter_cls_num.yml')
def iter_cls_num(uuid):
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
        type = app.config["PROJECT_INFO"][uuid]["front_project"]['type']
        # Get value of front
        iteration = request.get_json()['iteration']
        # Get class number
        num_info = count_dataset(prj_name, type, iteration)
        
        return jsonify(num_info)
