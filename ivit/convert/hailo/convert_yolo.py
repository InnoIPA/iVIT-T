import logging, os, shutil, sys
# Append to API
from pathlib import Path
from hailo_api import Hailo
sys.path.append(str(Path(__file__).resolve().parents[1]/""))
from common import MAIN_PATH, check_model
sys.path.append(str(Path(__file__).resolve().parents[3]/"common"))
from utils import cmd, read_json, write_json, ROOT


def convert_yolo(input_model_path:str, output_dir:str, export_dir:str, project_name:str, model_dict:dict, cfg_path:str, shape:list):
    arch = model_dict["model_config"]["arch"]
    cfgpath = model_dict["train_config"]["save_model_path"].split("weight")[0] + arch + ".cfg"

    # Convert weights to onnx
    logging.info('Start Convert...')
    logging.info('Convert Darknet to Onnx...')
    logging.info("Step:1/5,")
    command = "python3 {}/hailo/pytorch-YOLOv4/demo_darknet2onnx.py {} {} {}".format(MAIN_PATH, cfgpath, input_model_path, arch)
    cmd(command)
    # Move file to output_dir
    onnx_list = [ file for file in os.listdir(os.getcwd()) if "onnx" in file]
    onnx_path = onnx_list[0]
    onnx_output_path = output_dir + "/" + project_name + ".onnx"
    shutil.move(onnx_path, onnx_output_path)

    # Convert onnx to har
    logging.info('Onnx convert to Har...')
    logging.info("Step:2/5,")
    hailo = Hailo(project_name, onnx_output_path, "object_detection", shape)
    start_node = ["input"]
    if "tiny" in arch:
        end_node = ["/models.29/conv18/Conv", "/models.36/conv21/Conv"]
    else:
        end_node = ["/models.149/conv102/Conv", "/models.160/conv110/Conv", "/models.138/conv94/Conv"]
    hailo.parsing(start_node, end_node)

    # Quantize har
    logging.info('Quantize...')
    logging.info("Step:3/5,")
    hailo.optimization()

    # Compile hef
    logging.info('Compile to Hef...')
    logging.info("Step:4/5,")
    hailo.compile()

    # Check model is exist
    hef_path = output_dir + "/" + project_name + ".hef"
    status = check_model(hef_path, ".hef")
    if not status:
        return False
    
    # Move files in ./export
    logging.info("Step:5/5,")
    logging.info("Export model")
    shutil.copyfile(hef_path, export_dir + "/" + project_name + ".hef")
    # export classes.txt
    shutil.copyfile(model_dict["train_config"]["label_path"], export_dir + '/classes.txt')
    # export yolo.json
    shutil.copyfile(cfg_path, export_dir + '/yolo.json')

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