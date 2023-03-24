import logging, os, shutil, sys, yaml

# Append to API
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]/""))
sys.path.append(str(Path(__file__).resolve().parents[3]/"common"))
from utils import cmd, read_json, write_json, ROOT
from common.check import check_model

def convert_yolo(input_model:str, output_dir:str, model_name:str, export_dir:str, 
                        project_name:str, model_dict:dict, cfg_path:str, shape:list):

    h,w,c = shape
    arch = model_dict["model_config"]["arch"]
    m_name = model_name.split(".")[0]
    cfgpath = model_dict["train_config"]["save_model_path"].split("weight")[0] + arch + ".cfg"
    logging.info('Start converting...')
    logging.info('Convert Darknet to Tensorflow...')
    logging.info("Step:1/3,")
    command = "python3 convert/common/darknet2keras.py {} {} {}".format(cfgpath, input_model, output_dir)
    cmd(command)
    # Remove intel_model_anchors.txt
    intel_model_anchor = output_dir.split("intel_model")[0] + "intel_model_anchors.txt"
    if os.path.exists(intel_model_anchor):
        os.remove(intel_model_anchor)

    # Tensorflow2IR
    logging.info('Convert Tensorflow to OpenVINO...')
    logging.info("Step:2/3,")
    command = "mo --framework=tf --data_type=FP16 --saved_model_dir={} --output_dir={} --input_shape [1,{},{},{}] \
                    --input=image_input --scale_values=image_input[255] --reverse_input_channels \
                        --layout=image_input(NHWC) --model_name={}".format(output_dir, output_dir, h, w, c, m_name)
    cmd(command)

    # Check model is exist
    status = check_model(output_dir+"/"+m_name+".bin", ".bin")
    if not status:
        return False
    
    # Export bin/mapping/xml
    logging.info("Step:3/3,")
    logging.info("Export model")
    shutil.copyfile(output_dir+"/"+m_name+".bin", export_dir+ "/" + project_name + ".bin")
    shutil.copyfile(output_dir+"/"+m_name+".mapping", export_dir + "/" + project_name + ".mapping")
    shutil.copyfile(output_dir+"/"+m_name+".xml", export_dir + "/" + project_name + ".xml")
    # Export classes.txt
    shutil.copyfile(model_dict["train_config"]["label_path"], export_dir+'/classes.txt')
    # Export yolo.json
    shutil.copyfile(cfg_path, export_dir+'/yolo.json')

    # Added anchors in json
    logging.info("Added anchor in the Config...")
    f = open(cfgpath)
    text = f.read()
    anchor = text.split("anchors")[-1].split("\nclasses")[0].split("=")[-1].replace(" ", "")
    logging.info(anchor)
    f.close()
    orignal = read_json(export_dir+'/yolo.json')
    orignal["anchors"] = anchor
    write_json(export_dir+'/yolo.json', orignal)