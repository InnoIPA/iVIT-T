import logging, shutil, sys

# Append to API
from pathlib import Path
from hailo_api import Hailo
sys.path.append(str(Path(__file__).resolve().parents[1]/""))
from common import MAIN_PATH, check_model
sys.path.append(str(Path(__file__).resolve().parents[3]/"common"))
from utils import cmd, read_json, write_json, ROOT


def convert_cls(input_model:str, output_dir:str, export_dir:str, project_name:str, model_dict:dict, cfg_path:str, shape:list):
    
    h,w,c = shape
    output_model = input_model.split('.h5')[0]+".pb"
    output_model = output_dir + "/" + input_model.split('weights/')[-1].split('.h5')[0] + ".pb"
    split_output_model = output_model.split('project/')
    # keras2tensorflow
    logging.info('Start Converting...')
    logging.info('Convert Keras to Tensorflow...')
    logging.info("Step:1/5,")
    command = "python3 {}/common/keras2tensorflow.py --input_model {} --output_model {}".format(MAIN_PATH, input_model, output_model)
    cmd(command)
    # Check model is exist
    status = check_model(output_model, ".pb")
    if not status:
        return False

    # Convert pb to har
    logging.info('Convert Tensorflow to Hailo...')
    logging.info("Step:2/5,")
    hailo = Hailo(project_name, output_model, "classification", shape)
    start_node = ["import/input_1"]
    end_node = ["import/results/Softmax"]
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
    # export classification.json
    shutil.copyfile(cfg_path, export_dir + '/classification.json')