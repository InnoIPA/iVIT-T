from flask import Blueprint, request, jsonify, send_from_directory
from flasgger import swag_from
import logging
import os
from pathlib import Path
from natsort import natsorted
from webapi import app
from .common.utils import success_msg, error_msg, exists, YAML_MAIN_PATH
from .common.display_tool import count_dataset, workspace_path, iteration_path

app_dy_dt = Blueprint( 'display_dataset', __name__)
# Define API Docs path and Blue Print
YAML_PATH       = YAML_MAIN_PATH + "/display_dataset"

@app_dy_dt.route('/<uuid>/get_dataset', methods=['GET']) 
@swag_from("{}/{}".format(YAML_PATH, "get_dataset.yml"))
def get_dataset(uuid):
    # Check uuid is/isnot in app.config["PROJECT_INFO"]
    if not ( uuid in app.config["PROJECT_INFO"].keys()):
        return error_msg("UUID:{} does not exist.".format(uuid))
    # Get project name
    prj_name = app.config["PROJECT_INFO"][uuid]["front_project"]["project_name"]   

    prj_path = "./Project/"+prj_name
    folder_name = [ dir for dir in natsorted(os.listdir(prj_path)) if os.path.isdir(prj_path+"/"+dir)]
    return jsonify({"folder_name":folder_name}) 

@app_dy_dt.route('/<uuid>/filter_dataset', methods=['POST']) 
@swag_from("{}/{}".format(YAML_PATH, "filter_dataset.yml"))
def filter_dataset(uuid):
    if request.method == 'POST':
        # Check uuid is/isnot in app.config["PROJECT_INFO"]
        if not ( uuid in app.config["PROJECT_INFO"].keys()):
            return error_msg("UUID:{} does not exist.".format(uuid))
        # Check key of front
        if not "iteration" in request.get_json().keys():
            return error_msg("KEY:iteration does not exist.")
        elif not "class_name" in request.get_json().keys():
            return error_msg("KEY:class_name does not exist.")
        # Get project name
        prj_name = app.config["PROJECT_INFO"][uuid]["front_project"]["project_name"] 
        # Get value of front
        iteration = request.get_json()['iteration']
        class_name = request.get_json()['class_name']
        # Get type
        type = app.config["PROJECT_INFO"][uuid]["front_project"]['type']
        # Give img path
        iter_path = "./Project/"+prj_name+"/"+iteration
        # Check iteration
        if "workspace" == iteration:
            return jsonify(workspace_path(class_name, iter_path, type))
        else:
            return jsonify(iteration_path(class_name, iter_path, type))

@app_dy_dt.route('/display_img/<path:path>', methods=['GET'])
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
        return error_msg("This image does not exist:{}".format(path+"/"+path_list[-1]))

@app_dy_dt.route('/<uuid>/display_url', methods=['POST'])
@swag_from("{}/{}".format(YAML_PATH, "display_url.yml"))
def display_url(uuid):
    if request.method == 'POST':
        # Check uuid is/isnot in app.config["PROJECT_INFO"]
        if not ( uuid in app.config["PROJECT_INFO"].keys()):
            return error_msg("UUID:{} does not exist.".format(uuid))
        # Check key of front
        if not "iteration" in request.get_json().keys():
            return error_msg("KEY:iteration does not exist.")
        elif not "class_name" in request.get_json().keys():
            return error_msg("KEY:class_name does not exist.")
        # Get project name
        prj_name = app.config["PROJECT_INFO"][uuid]["front_project"]["project_name"] 
        # Get value of front
        iteration = request.get_json()['iteration']
        class_name = request.get_json()['class_name']
        # Get type
        type = app.config["PROJECT_INFO"][uuid]["front_project"]['type']
        # Give img path
        iter_path = "./Project/" + prj_name+"/"+iteration
        # Check iteration
        url = "http://{}:{}".format(request.environ['SERVER_NAME'], request.environ['SERVER_PORT'])
        if "workspace" == iteration:
            img_path = workspace_path(class_name, iter_path, type)
            img_path = [ url + "/display_img/"+ path.split("./")[-1] for path in img_path["img_path"]]
            return jsonify({"img_path":img_path})
        else:
            img_path = iteration_path(class_name, iter_path, type)
            img_path = [ url + "/display_img/"+ path.split("./")[-1] for path in img_path["img_path"]]
            return jsonify({"img_path":img_path})

@app_dy_dt.route('/<uuid>/delete_img', methods=['DELETE']) 
@swag_from("{}/{}".format(YAML_PATH, "delete_img.yml"))
def delete_img(uuid):
    if request.method == 'DELETE':
        # Check uuid is/isnot in app.config["PROJECT_INFO"]
        if not ( uuid in app.config["PROJECT_INFO"].keys()):
            return error_msg("UUID:{} does not exist.".format(uuid))
        # Check key of front
        if not "image_info" in request.get_json().keys():
            return error_msg("KEY:image_info does not exist.")
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
                    if type == 'object_detection' and os.path.isfile("./Project/"+prj_name+"/workspace"+'/'+label+'/'+ os.path.splitext(name)[0] + '.txt'):
                        logging.info("Removed:{}".format("./Project/"+prj_name+"/workspace"+'/'+label+'/'+ os.path.splitext(name)[0] + '.txt'))
                        os.remove("./Project/"+prj_name+"/workspace"+'/'+label+'/'+ os.path.splitext(name)[0] + '.txt')

        return success_msg("Delete images- project:{}, images:{}".format(prj_name, image_info_list))

@app_dy_dt.route('/<uuid>/iter_cls_num', methods=['POST']) 
@swag_from("{}/{}".format(YAML_PATH, "iter_cls_num.yml")) 
def iter_cls_num(uuid):
    if request.method == 'POST':
        # Check uuid is/isnot in app.config["PROJECT_INFO"]
        if not ( uuid in app.config["PROJECT_INFO"].keys()):
            return error_msg("UUID:{} does not exist.".format(uuid))
        # Check key of front
        if not "iteration" in request.get_json().keys():
            return error_msg("KEY:iteration does not exist.")
        # Get project name
        prj_name = app.config["PROJECT_INFO"][uuid]["front_project"]["project_name"] 
        # Get type
        type = app.config["PROJECT_INFO"][uuid]["front_project"]['type']
        # Get value of front
        iteration = request.get_json()['iteration']
        # Get class number
        num_info = count_dataset(prj_name, type, iteration)
        
        return jsonify(num_info)
