# Copyright (c) 2023 Innodisk Corporation
# 
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

import logging, shutil, sys, os

# Append to API
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]/""))
from common import MAIN_PATH, check_model
sys.path.append(str(Path(__file__).resolve().parents[2]/"common"))
from utils import cmd

def keras2nvidia(input_model:str, output_dir:str, model_name:str, export_dir:str, project_name:str, model_dict:dict, cfg_path:str):
    logging.info('Start Converting...')
    logging.info('Convert Keras to ONNX...')
    logging.info("Step:1/2,")
    command = "python3 {}/common/keras2onnx.py \
                            --keras_model_file {} --output_file {} --op_set {}".format( MAIN_PATH,
                                                                                        input_model,
                                                                                        os.path.join(output_dir, model_name.split(".")[0] + ".onnx"),
                                                                                        13)

    # Run command
    cmd(command)

    # Check model is exist
    m_name = model_name.split(".")[0]
    status = check_model(output_dir+"/"+m_name+".onnx", ".onnx")
    if not status:
        return False
    
    #export .onnx
    logging.info("Step:2/2,")
    logging.info("Export model")
    shutil.copyfile(output_dir+"/"+m_name+".onnx", export_dir+"/"+project_name+".onnx")
    #export classes.txt
    shutil.copyfile(model_dict["train_config"]["label_path"], export_dir+'/classes.txt')
    #export classification.json
    shutil.copyfile(cfg_path, export_dir+'/classification.json')

def convert_yolo(input_model:str, output_dir:str, export_dir:str, project_name:str, model_dict:dict, cfg_path:str):

    arch = model_dict["model_config"]["arch"]
    #export weights
    logging.info("Step:1/1,")
    logging.info("Export model")
    shutil.copyfile(input_model, export_dir+"/"+project_name+".weights")
    #export classes.txt
    shutil.copyfile(model_dict["train_config"]["label_path"], export_dir+'/classes.txt')
    #export yolo.cfg
    shutil.copyfile(cfg_path.split("yolo.json")[0]+'/'+arch+'.cfg', export_dir+'/'+project_name+'.cfg')
    #export yolo.json
    shutil.copyfile(cfg_path, export_dir+'/yolo.json')
    # rm null dir
    os.rmdir(output_dir)