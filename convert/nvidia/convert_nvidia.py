import sys, os, argparse, time, shutil, logging
# Append to API

from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[2]/"common"))
from logger import config_logger
from utils import read_json 

from convert_cls import convert_cls
from convert_yolo import convert_yolo

def main(args):
    # Read model_json
    model_dict = read_json(args.config)
    model_list = os.listdir(model_dict["train_config"]["save_model_path"])
    model_name = [best for best in model_list if "best" in best][0]
    input_model = model_dict["train_config"]["save_model_path"] +'/'+ model_name
    output_dir = model_dict["train_config"]["save_model_path"]+'/nvidia_model'
    export_dir = model_dict["train_config"]["save_model_path"].split("weights")[0]+'export'
    project_name = args.config.split("project/")[-1].split("/")[0]
    start = time.time()

	# Create target Directory
    if os.path.isdir(export_dir):
        shutil.rmtree(export_dir)
    try:
        os.makedirs(output_dir, exist_ok=True, mode=0o777)
        os.makedirs(export_dir, exist_ok=True, mode=0o777)

    except Exception as exc:
        logging.warn(exc)
        pass

    # keras convert	to onnx	
    if "classification" in args.config:
        convert_cls(input_model, output_dir, model_name, export_dir, project_name, model_dict, args.config)

    elif "yolo" in args.config:
        convert_yolo(input_model, output_dir, export_dir, project_name, model_dict, args.config)

	# Computing time
    end = time.time()
    logging.warning("Converting total time:{}".format(end - start))
    # logging.info('Converted.')

if __name__ == '__main__':
    config_logger('./convert.log', 'a', "info")
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', help = "The path of model config")
    args = parser.parse_args()
    sys.exit(main(args) or 0)