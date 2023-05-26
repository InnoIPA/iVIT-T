from flask import Blueprint, request, jsonify, send_from_directory
from flasgger import swag_from
import logging, os, shutil
from pathlib import Path
from natsort import natsorted
from webapi import app
from .common.utils import success_msg, error_msg, exists, get_classes_list
from .common.config import ROOT, YAML_MAIN_PATH
from .common.upload_tools import create_class_dir, Upload_DB
from .common.display_tool import count_dataset, get_img_path_db, check_unlabeled_images
from .common.database import delete_data_table_cmd, execute_db, update_data_table_cmd
from .common.inspection import Check
app_dy_dt = Blueprint( 'display_dataset', __name__)
# Define API Docs path and Blue Print
YAML_PATH       = YAML_MAIN_PATH + "/display_dataset"
chk = Check()

@app_dy_dt.route('/<uuid>/get_dataset', methods=['GET']) 
@swag_from("{}/{}".format(YAML_PATH, "get_dataset.yml"))
def get_dataset(uuid):
    # Check uuid is/isnot in app.config["PROJECT_INFO"]
    if not ( uuid in app.config["PROJECT_INFO"].keys()):
        return error_msg("UUID:{} does not exist.".format(uuid))
    # Get project name
    prj_name = app.config["PROJECT_INFO"][uuid]["project_name"]   
    # Get all dataset/iteration from project
    prj_path = ROOT + '/' +prj_name
    if not exists(prj_path):
        return error_msg("The project does not exist:[{}]".format(prj_name))
    folder_name = [ dir for dir in natsorted(os.listdir(prj_path)) if os.path.isdir(prj_path+"/"+dir)]
    # Arrange folder name from the index
    folder_name = [ "iteration"+str(idx+1) for idx, dir in enumerate(natsorted(folder_name)) if "iteration" in dir]
    folder_name.append("workspace")
    logging.info("Get path of dataset from project:[{}]".format(prj_name))
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
        prj_name = app.config["PROJECT_INFO"][uuid]["project_name"] 
        # Get value of front
        iteration = request.get_json()['iteration']
        class_name = request.get_json()['class_name']
        # Mapping iteration
        if iteration != "workspace":
            iteration = chk.mapping_iteration(uuid, prj_name, iteration, front=True)
            if "error" in iteration:
                return error_msg(str(iteration[1]))
        # Get img path
        dict_img_path = get_img_path_db(uuid, prj_name, iteration, class_name, front=False)
        # Prevent error 
        if "error" in dict_img_path:
            return error_msg(str(dict_img_path[1]))
        logging.info("Get the image path of this class:[{}] in the project:[{}]".format(class_name, prj_name))
        return jsonify(dict_img_path)

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
        prj_name = app.config["PROJECT_INFO"][uuid]["project_name"] 
        # Get value of front
        iteration = request.get_json()['iteration']
        class_name = request.get_json()['class_name']
        # Mapping iteration
        if iteration != "workspace":
            iteration = chk.mapping_iteration(uuid, prj_name, iteration, front=True)
            if "error" in iteration:
                return error_msg(str(iteration[1]))
        # Get img path
        dict_img_path = get_img_path_db(uuid, prj_name, iteration, class_name, front=False)
        # Prevent error 
        if "error" in dict_img_path:
            return error_msg(str(dict_img_path[1]))
        # Setting url
        url = "http://{}:{}".format(app.config["HOST"], request.environ['SERVER_PORT'])
        img_path = [ url + "/display_img/"+ path.split("./")[-1] for path in dict_img_path["img_path"]]
        logging.info("Get the image url of this class:[{}] in the project:[{}]".format(class_name, prj_name))
        return jsonify({"img_path":img_path})

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
        prj_name = app.config["PROJECT_INFO"][uuid]["project_name"] 
        # Get type
        type = app.config["PROJECT_INFO"][uuid]['type']
        # Get value of front
        image_info_list = request.get_json()['image_info']
        # Loop dictionary key
        for key in image_info_list.keys(): 
            if key == "Unlabeled" or type == "object_detection":
                label = ""
            else:
                label = key
            # Check folder does exist
            if os.path.isdir(ROOT + '/' +prj_name+"/workspace"+'/'+label):
                for name in image_info_list[key]:
                    # Remove files
                    if os.path.isfile(ROOT + '/' +prj_name+"/workspace"+'/'+label+'/'+name):
                        logging.info("Removed:[{}]".format(prj_name+"/workspace"+'/'+label+'/'+name))
                        os.remove(ROOT + '/' +prj_name+"/workspace"+'/'+label+'/'+name)
                        # Delete data from Database
                        command = delete_data_table_cmd("workspace", "project_uuid=\'{}\' AND img_path=\'{}\'".format(uuid, label+'/'+name))
                        info_db = execute_db(command, True)
                        if info_db is not None:
                            return error_msg(str(info_db[1]))
                        # Update project of Database
                        update = Upload_DB(uuid, prj_name, type, label, "", "")
                        error_db = update.update_prj_db()
                        # Prevent error 
                        if error_db:
                            return error_msg(str(error_db[1]))
                    else:
                        logging.error("This image:[{}] does not exist in workspace.".format(label+'/'+name))

                    # Object_detection remove txt
                    if type == 'object_detection' and os.path.isfile(ROOT + '/' +prj_name+"/workspace"+'/'+label+'/'+ os.path.splitext(name)[0] + '.txt'):
                        logging.info("Removed:{}".format(ROOT + '/' +prj_name+"/workspace"+'/'+label+'/'+ os.path.splitext(name)[0] + '.txt'))
                        os.remove(ROOT + '/' +prj_name+"/workspace"+'/'+label+'/'+ os.path.splitext(name)[0] + '.txt')
            else:
                return error_msg("The class:[{}] does not exist in the project:[{}]".format(key, prj_name))

        return success_msg("Delete images:[{}] in project:[{}]".format(image_info_list, prj_name))

@app_dy_dt.route('/<uuid>/delete_all_img', methods=['DELETE']) 
@swag_from("{}/{}".format(YAML_PATH, "delete_all_img.yml"))
def delete_all_img(uuid):
    if request.method == 'DELETE':
        # Check uuid is/isnot in app.config["PROJECT_INFO"]
        if not ( uuid in app.config["PROJECT_INFO"].keys()):
            return error_msg("UUID:{} does not exist.".format(uuid))
        # Get project name
        prj_name = app.config["PROJECT_INFO"][uuid]["project_name"] 
        # Get type
        type = app.config["PROJECT_INFO"][uuid]['type']
        # Check folder does exist
        main_path = os.path.join(ROOT, prj_name)
        ws_path = os.path.join(main_path, "workspace")
        if os.path.isdir(ws_path):
            temp_classes_path = os.path.join(main_path, "classes.txt")
            # Catch classes.txt
            shutil.move(os.path.join(ws_path, "classes.txt"), temp_classes_path)
            # Delete workspace
            shutil.rmtree(ws_path)
            # Create new folder
            create_class_dir("Unlabeled", prj_name, type)
            # Create new class foler
            if type == "classification":
                classes_list = get_classes_list(temp_classes_path)
                for cls in classes_list:
                    create_class_dir(cls, prj_name, type)
            # move classes.txt
            shutil.move(temp_classes_path, os.path.join(ws_path, "classes.txt"))
            # Delete ws table in db
            command = delete_data_table_cmd("workspace", "project_uuid=\'{}\'".format(uuid))
            info_db = execute_db(command, True)
            if info_db is not None:
                return error_msg(str(info_db[1]))
            # Remove covert images
            cover_list = [ main_path + "/" + name for name in os.listdir(main_path) if "cover" in name]
            if len(cover_list) > 0 and exists(cover_list[0]):
                os.remove(cover_list[0])
            # Update prj table in db
            values = "effect_img_nums=0, unlabeled_img_nums=0, show_image_path=\'\'"
            select = "project_uuid=\'{}\'".format(uuid)
            command = update_data_table_cmd("project", values, select)
            info_db = execute_db(command, True)
            if info_db is not None:
                return error_msg(str(info_db[1]))
            return success_msg("Delete All images in Project:[{}]".format(prj_name))
        else:
            return error_msg("The project have problem:[{}].".format(prj_name))

@app_dy_dt.route('/<uuid>/iter_class_num', methods=['POST'])
@swag_from("{}/{}".format(YAML_PATH, "iter_class_num.yml")) 
def iter_class_num(uuid):
    if request.method == 'POST':
        # Check uuid is/isnot in app.config["PROJECT_INFO"]
        if not ( uuid in app.config["PROJECT_INFO"].keys()):
            return error_msg("UUID:{} does not exist.".format(uuid))
        # Check key of front
        if not "iteration" in request.get_json().keys():
            return error_msg("KEY:iteration does not exist.")
        # Get project name
        prj_name = app.config["PROJECT_INFO"][uuid]["project_name"] 
        # Get value of front
        iteration = request.get_json()['iteration']
        # Get type
        type = app.config["PROJECT_INFO"][uuid]['type']
        # Check unlabeled images
        logging.warning("Get API of iter_class_num :[iteration:{}, type:{}]".format(iteration, type))
        if iteration== "workspace":
            info_db = check_unlabeled_images(uuid, prj_name, iteration)
            if "error" in info_db:
                return error_msg(str(info_db[1]))
        else:
            # Mapping iteration
            iteration = chk.mapping_iteration(uuid, prj_name, iteration, front=True)
            if "error" in iteration:
                return error_msg(str(iteration[1]))
        # Get class number
        num_info = count_dataset(uuid, prj_name, iteration, front=False)
        if "error" in num_info:
            return error_msg(str(num_info[1]))
        logging.info("Get numbers of dataset in project:[{}:{}]:{}".format(iteration, prj_name, num_info))
        return jsonify(num_info)
