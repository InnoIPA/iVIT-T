from flask import Blueprint,request
import requests , time , psutil ,json
# requests.adapters.DEFAULT_RETRIES = 5
from flasgger import swag_from
import sys
import logging, os, shutil
from webapi import app
from .common.utils import success_msg, error_msg 
from .common.config import ALLOWED_EXTENSIONS, YAML_MAIN_PATH,ROOT, EVAL_VAL,AUTOLABEL_VAL
from .common.upload_tool import create_class_dir, filename_processing, save_file, Upload_DB, add_class_filename
from .common.inspection import Check
from .common.evaluate_tool import Evaluate,threshold_process, temp_label_data_db

chk = Check()

app_ud_dt = Blueprint( 'upload_dataset', __name__)
# Define API Docs path and Blue Print
YAML_PATH       = YAML_MAIN_PATH + "/upload_dataset"
@app_ud_dt.route('/<uuid>/upload', methods=['POST']) 
@swag_from("{}/{}".format(YAML_PATH, "upload.yml"))
def upload(uuid):
    # Check uuid is/isnot in app.config["PROJECT_INFO"]
    if not ( uuid in app.config["PROJECT_INFO"].keys()):
        return error_msg(400, {}, "UUID:{} does not exist.".format(uuid), log=True)
    # Get project name
    prj_name = app.config["PROJECT_INFO"][uuid]["project_name"]
    # Get type
    type = app.config["PROJECT_INFO"][uuid]["type"]
    # Collect filename
    collect_filename = []
    # Files is multi folder 
    for key in request.files.keys():
        # Setting save path
        label, dir_path = create_class_dir(key, prj_name, type)
        # Get files in files.getlist
        files = request.files.getlist(key)
        # Files is empty
        if not files:
            if os.path.isdir(dir_path):
                shutil.rmtree('{}'.format(dir_path, ignore_errors=True))
            return error_msg(400, {}, "No upload files in project:[{}]".format(prj_name), log=True)
        # Get fileinfo/filename in files
        for file in files:
            if file:
                # Get file name
                filename = filename_processing(file,False)
                # Save file
                if type == "classification":
                    filename = add_class_filename(str(key), str(filename))
                    # Skip other format exclude image format
                    if not (filename.split(".")[-1] in ALLOWED_EXTENSIONS["image"]):
                        return error_msg(400, {}, "This type of filename is not allowed:[{}:{}]".format(filename, filename.split(".")[-1]), log=True)
                    # Save image
                    status, filename = save_file(file, dir_path, filename)
                elif type == "object_detection":
                    # Skip other format exclude image format
                    if (not (filename.split(".")[-1] in ALLOWED_EXTENSIONS["label"])) and (not (filename.split(".")[-1] in ALLOWED_EXTENSIONS["image"])):
                        return error_msg(400, {}, "This type of filename is not allowed:[{}:{}]".format(filename.split(".")[-1], filename), log=True) 
                    # Save image and annotation
                    status, filename = save_file(file, dir_path, filename)
                # Remove file size is 0
                if os.stat(dir_path+"/"+filename).st_size == 0:
                    os.remove(dir_path+"/"+filename)
                    return error_msg(400, {}, "The size of file is 0.:[{}]".format(filename), log=True)
                
                # The status of save image prevent to write twice db
                if status:
                    # Update db
                    updb = Upload_DB(uuid, prj_name, type, label, dir_path, filename)
                    if (filename == "classes.txt") or (filename == "classes_temp.txt"):
                        # error_db = compare_classes(dir_path, uuid)
                        # if error_db:
                        #     return error_msg(400, {}, str(error_db[1]))
                        pass
                    else:
                        error_db = updb.upload_fillin_ws_info()
                        if error_db:
                            return error_msg(400, {}, str(error_db[1]))

                    # Append to list
                    collect_filename.append(filename)
            else:
                error_msg(400, {}, "The file is null:[{}]".format(filename), log=True)
    return success_msg(200, {}, "Success", "Upload files-[{}:{}, numbers:{}, file_list:{}]".format(prj_name, label, len(files), collect_filename))
# @app_ud_dt.route('/<uuid>/upload', methods=['POST']) 
# @swag_from("{}/{}".format(YAML_PATH, "upload.yml"))
# def upload(uuid):
#     # Check uuid is/isnot in app.config["PROJECT_INFO"]
#     if not ( uuid in app.config["PROJECT_INFO"].keys()):
#         return error_msg(400, {}, "UUID:{} does not exist.".format(uuid), log=True)
#     # Get project name
#     prj_name = app.config["PROJECT_INFO"][uuid]["project_name"]
#     # Get type
#     type = app.config["PROJECT_INFO"][uuid]["type"]
#     # Collect filename
#     collect_filename = []
#     # Files is multi folder 

#     for key in request.files.keys():
#         # Setting save path
#         label, dir_path = create_class_dir(key, prj_name, type)
#         # Get files in files.getlist
#         files = request.files.getlist(key)
#         # Files is empty
#         if not files:
#             if os.path.isdir(dir_path):
#                 shutil.rmtree('{}'.format(dir_path, ignore_errors=True))
#             return error_msg(400, {}, "No upload files in project:[{}]".format(prj_name), log=True)
#         # Get fileinfo/filename in files
#         for file in files:
#             if file:
#                 # Get file name
#                 filename = filename_processing(file,False)
#                 # Save file
#                 if type == "classification":
#                     filename = add_class_filename(str(key), str(filename))
#                     # Skip other format exclude image format
#                     if not (filename.split(".")[-1] in ALLOWED_EXTENSIONS["image"]):
#                         return error_msg(400, {}, "This type of filename is not allowed:[{}:{}]".format(filename, filename.split(".")[-1]), log=True)
#                     # Save image
#                     status, filename = save_file(file, dir_path, filename)
#                     AUTOLABEL_VAL.append(os.path.join(dir_path, filename))
#                 elif type == "object_detection":
#                     # Skip other format exclude image format
#                     if (not (filename.split(".")[-1] in ALLOWED_EXTENSIONS["label"])) and (not (filename.split(".")[-1] in ALLOWED_EXTENSIONS["image"])):
#                         return error_msg(400, {}, "This type of filename is not allowed:[{}:{}]".format(filename.split(".")[-1], filename), log=True) 
#                     # Save image and annotation
#                     status, filename = save_file(file, dir_path, filename)
#                     AUTOLABEL_VAL.append(os.path.join(dir_path, filename))
#                 # Remove file size is 0
#                 if os.stat(dir_path+"/"+filename).st_size == 0:
#                     os.remove(dir_path+"/"+filename)
#                     return error_msg(400, {}, "The size of file is 0.:[{}]".format(filename), log=True)
                
#                 # The status of save image prevent to write twice db
#                 if status:
#                     # Update db
#                     updb = Upload_DB(uuid, prj_name, type, label, dir_path, filename)
#                     if (filename == "classes.txt") or (filename == "classes_temp.txt"):
#                         # error_db = compare_classes(dir_path, uuid)
#                         # if error_db:
#                         #     return error_msg(400, {}, str(error_db[1]))
#                         pass
#                     else:
#                         error_db = updb.upload_fillin_ws_info()
#                         if error_db:
#                             return error_msg(400, {}, str(error_db[1]))

#                     # Append to list
#                     collect_filename.append(filename)
#             else:
#                 error_msg(400, {}, "The file is null:[{}]".format(filename), log=True)


#     #----------autolabeling---------------------
    
#     # eval = Evaluate()

#     # img_key ="custom"

#     # # Get model.json
#     # if type == "object_detection":
#     #     model = "yolo"
#     # elif type == "classification":
#     #     model = type

#     # # check this project have best model
#     # front_iteration = "iteration1"
#     # try:
#     #     dir_iteration = chk.mapping_iteration(uuid, prj_name, front_iteration, front=True)
#     # except:
#     #     print(error_msg(400, {}, str(dir_iteration[1]), log=True))

#     # # Setting evaluate.json
#     # msg = eval.set_eval_json(prj_name, dir_iteration, model, autokey=True, img_key=img_key)
#     # if msg:
#     #     print(error_msg(400, {}, "{}:[{}:{}]".format(msg, prj_name, front_iteration), log=True))
    
#     # # Evaluate
#     # command = "python3 adapter.py -c {} --eval --autolabel_upload".format(ROOT + '/' +prj_name+'/'+ dir_iteration + '/'+ model + '.json')
#     # # Run command
#     # eval.thread_eval(uuid, type, command)
#     # result = eval.cmd_q.get()
#     # if "Error" in result.keys():
#     #     print(error_msg(400, result["Error"], "Out of memory", log=True))
#     # EVAL_VAL[uuid] = result
#     # # Threshold / Rearrange
#     # threshold = 0
#     # log_dict = threshold_process(uuid, prj_name, threshold)
#     # # Save database
#     # error_db = temp_label_data_db(uuid, prj_name, log_dict)
#     # if error_db:
#     #     print(error_msg(400, {}, error_db[1], log=True))
                    

#     return success_msg(200, {}, "Success", "Upload files-[{}:{}, numbers:{}, file_list:{}]".format(prj_name, label, len(files), collect_filename))
