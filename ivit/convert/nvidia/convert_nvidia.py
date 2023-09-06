import sys, os, time, shutil, logging

# Append to API
from .nvidia_api import keras2nvidia, convert_yolo
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[2]/"common"))
from utils import read_json 

def converting_nvidia(config:str):
    # Read model_json
    model_dict = read_json(config)
    model_list = os.listdir(model_dict["train_config"]["save_model_path"])
    model_name = [best for best in model_list if "best" in best][0]
    input_model = model_dict["train_config"]["save_model_path"] +'/'+ model_name
    output_dir = model_dict["train_config"]["save_model_path"]+'/nvidia_model'
    export_dir = model_dict["train_config"]["save_model_path"].split("weights")[0]+'export'
    project_name = config.split("project/")[-1].split("/")[0]
    start = time.time()

	# Create target Directory
    if os.path.isdir(export_dir):
        shutil.rmtree(export_dir)
    if os.path.isdir(output_dir):
        shutil.rmtree(output_dir)
    try:
        os.makedirs(output_dir, exist_ok=True, mode=0o777)
        os.makedirs(export_dir, exist_ok=True, mode=0o777)

    except Exception as exc:
        logging.warn(exc)
        pass

    # keras convert	to onnx	
    if "classification" in config or "unet" in config:
        keras2nvidia(input_model, output_dir, model_name, export_dir, project_name, model_dict, config)

    elif "yolo" in config:
        convert_yolo(input_model, output_dir, export_dir, project_name, model_dict, config)

	# Computing time
    end = time.time()
    logging.warning("Converting total time: {} s".format(round(end - start, 3)))
