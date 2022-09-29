from flask import Blueprint, request
from flasgger import swag_from
import logging
import os, shutil
from webapi import app
from werkzeug.utils import secure_filename
from .common.utils import success_msg, error_msg, ALLOWED_EXTENSIONS, YAML_MAIN_PATH

app_ud_dt = Blueprint( 'upload_dataset', __name__)
# Define API Docs path and Blue Print
YAML_PATH       = YAML_MAIN_PATH + "/upload_dataset"

@app_ud_dt.route('/<uuid>/upload', methods=['POST']) 
@swag_from("{}/{}".format(YAML_PATH, "upload.yml"))
def upload(uuid):
    if request.method == 'POST':
        logging.info('Upload file.')
        # Check uuid is/isnot in app.config["PROJECT_INFO"]
        if not ( uuid in app.config["PROJECT_INFO"].keys()):
            return error_msg("UUID:{} is not exist.".format(uuid))
        # Get project name
        prj_name = app.config["PROJECT_INFO"][uuid]["front_project"]["project_name"]
        # Get type
        type = app.config["PROJECT_INFO"][uuid]["front_project"]["type"]
        
        # files is multi folder 
        for key in request.files.keys():
            # Setting save path
            if key == "Unlabeled" or type == "object_detection":
                dirs = ""
            else:
                dirs = key

            dir_path = "./Project/"+prj_name+"/workspace/"+dirs
            # Create target Directory
            try:
                os.makedirs(dir_path, exist_ok=True, mode=0o777)
            except Exception as exc:
                logging.warn(exc)
                pass
            
            # Get files in files.getlist
            files = request.files.getlist(key)
            # if is empty
            if not files:
                logging.error("This files is null-{}".format(dir_path))
                if os.path.isdir(dir_path):
                    shutil.rmtree('{}'.format(dir_path, ignore_errors=True))
                return error_msg("No upload files.")

            # Get filename in files
            for file in files:
                if file:
                    # Get file name
                    filename = secure_filename(file.filename)
                    # Check folder file
                    if "/" in file.name:
                        filename = file.name.split("/")[1]
                    # Exclude over 2 word(".") rename filename
                    split = filename.split(".")
                    if len(split)>2:
                        new_name = ""
                        for idx, word in enumerate(split):
                            if idx == 0:
                                new_name = word
                            elif idx < len(split)-1:
                                new_name = new_name + "_" + word
                            else:
                                new_name = new_name + "." + word
                        filename = new_name

                    if type == "classification":
                        # Skip other format exclude image format
                        if not (filename.split(".")[-1] in ALLOWED_EXTENSIONS["image"]):
                            logging.error("This type:{} of filename:{} ".format(filename.split(".")[-1], filename))
                            continue
                        
                        # Save image
                        file.save(os.path.join(dir_path, filename))

                    elif type == "object_detection":
                        # Skip other format exclude image format
                        if (not (filename.split(".")[-1] in ALLOWED_EXTENSIONS["label"])) and (not (filename.split(".")[-1] in ALLOWED_EXTENSIONS["image"])):
                            logging.error("This type:{} of filename:{} ".format(filename.split(".")[-1], filename))                            
                            continue

                        # Save image and annotation
                        file.save(os.path.join(dir_path, filename))

                    # Remove file size is 0
                    if os.stat(dir_path+"/"+filename).st_size == 0:
                        os.remove(dir_path+"/"+filename)
                        return error_msg("The size of {} is 0".format(filename))

        return success_msg("Upload images-{} images in {}/{}".format(len(files), prj_name, dirs))
