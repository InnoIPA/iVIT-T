from flask import Blueprint, request
from flasgger import swag_from
import logging, os, shutil
from webapi import app
from .common.utils import success_msg, error_msg
from .common.config import ALLOWED_EXTENSIONS, YAML_MAIN_PATH
from .common.upload_tools import create_class_dir, filename_processing, save_file, Upload_DB
app_ud_dt = Blueprint( 'upload_dataset', __name__)
# Define API Docs path and Blue Print
YAML_PATH       = YAML_MAIN_PATH + "/upload_dataset"

@app_ud_dt.route('/<uuid>/upload', methods=['POST']) 
@swag_from("{}/{}".format(YAML_PATH, "upload.yml"))
def upload(uuid):
    if request.method == 'POST':
        # Check uuid is/isnot in app.config["PROJECT_INFO"]
        if not ( uuid in app.config["PROJECT_INFO"].keys()):
            return error_msg("UUID:{} does not exist.".format(uuid))
        # Get project name
        prj_name = app.config["PROJECT_INFO"][uuid]["project_name"]
        # Get type
        type = app.config["PROJECT_INFO"][uuid]["type"]
        # Collect filename
        col_filename = []
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
                return error_msg("No upload files in project:[{}]".format(prj_name))
            # Get fileinfo/filename in files
            for file in files:
                if file:
                    # Get file name
                    filename = filename_processing(file)
                    # Save file
                    if type == "classification":
                        # Skip other format exclude image format
                        if not (filename.split(".")[-1] in ALLOWED_EXTENSIONS["image"]):
                            return error_msg("This type:[{}] of filename:[{}] ".format(filename.split(".")[-1], filename))
                        # Save image
                        status = save_file(file, dir_path, filename)

                    elif type == "object_detection":
                        # Skip other format exclude image format
                        if (not (filename.split(".")[-1] in ALLOWED_EXTENSIONS["label"])) and (not (filename.split(".")[-1] in ALLOWED_EXTENSIONS["image"])):
                            return error_msg("This type:[{}] of filename:[{}] ".format(filename.split(".")[-1], filename)) 
                        # Save image and annotation
                        status = save_file(file, dir_path, filename)
                        
                    # Remove file size is 0
                    if os.stat(dir_path+"/"+filename).st_size == 0:
                        os.remove(dir_path+"/"+filename)
                        return error_msg("The size of file is 0:[{}]".format(filename))
                    
                    # The status of save image prevent to write twice db
                    if status:
                        # Update db
                        updb = Upload_DB(uuid, prj_name, type, label, dir_path, filename)
                        if filename != "classes.txt":
                            info = updb.upload_fillin_ws_info()
                            if info is not None:
                                return error_msg(str(info[1]))
                        # Append to list
                        col_filename.append(filename)
                else:
                    error_msg("The file is null:[{}]".format(filename))

        return success_msg("Upload {} files:{} in [{}/{}]".format(len(files), col_filename, prj_name, label))