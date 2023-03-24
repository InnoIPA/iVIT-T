import logging, os, shutil, sys


# Append to API
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]/""))
sys.path.append(str(Path(__file__).resolve().parents[3]/"common"))
from utils import cmd, ROOT
from common.check import check_model

def convert_cls(input_model:str, output_dir:str, model_name:str, export_dir:str, 
                        project_name:str, model_dict:dict, cfg_path:str, shape:list):

    h,w,c = shape
    logging.info('Start converting...')
    logging.info('Convert Keras to Tensorflow...')
    logging.info("Step:1/3,")
    output_model = input_model.split('.h5')[0]+".pb"
    output_model = output_dir +"/"+ input_model.split('weights/')[-1].split('.h5')[0]+".pb"
    split_output_model = output_model.split('project/')
    # keras2tensorflow
    command = "python3 convert/common/keras2tensorflow.py --input_model {} --output_model {}".format(input_model, output_model)
    cmd(command)

    # Check model is exist
    status = check_model(output_model, ".pb")
    if not status:
        return False
        
    # Tensorflow2IR
    logging.info('Convert Tensorflow to OpenVINO...')
    logging.info("Step:2/3,")
    command = "mo --framework=tf --data_type=FP16 --input_model {} --output_dir {} --input_shape [1,{},{},{}] \
                        --mean_values=[123.68,116.78,103.94] --disable_nhwc_to_nchw".format(ROOT + split_output_model[-1], 
                                                                                            ROOT + output_dir.split('project/')[-1],
                                                                                            c,h,w)
    cmd(command)

    # Check model is exist
    m_name = model_name.split(".")[0]
    status = check_model(output_dir+"/"+m_name+".bin", ".bin")
    if not status:
        return False
    
    #export bin/mapping/xml
    logging.info("Step:3/3,")
    logging.info("Export model")
    shutil.copyfile(output_dir+"/"+m_name+".bin", export_dir+"/"+project_name+".bin")
    shutil.copyfile(output_dir+"/"+m_name+".mapping", export_dir+"/"+project_name+".mapping")
    shutil.copyfile(output_dir+"/"+m_name+".xml", export_dir+"/"+project_name+".xml")
    #export classes.txt
    shutil.copyfile(model_dict["train_config"]["label_path"], export_dir+'/classes.txt')
    #export classification.json
    shutil.copyfile(cfg_path, export_dir+'/classification.json')