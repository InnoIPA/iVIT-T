import sys, os, argparse, shutil, logging, time
# Append to API
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[2]/"common"))
from logger import config_logger
from utils import read_json, write_json

INTEL_VERSION = "openvino_2021.4.752"
INTEL_CONVERT_PATH = "/opt/intel/{}/deployment_tools".format(INTEL_VERSION)

def main(args):
	# Read model_json
	model_dict = read_json(args.config)
	model_list = os.listdir(model_dict["train_config"]["save_model_path"])
	model_name = [best for best in model_list if "best" in best][0]
	input_model = model_dict["train_config"]["save_model_path"] +'/'+ model_name
	output_dir = model_dict["train_config"]["save_model_path"]+'/intel_model'
	export_dir = model_dict["train_config"]["save_model_path"].split("weights")[0]+'export'
	shape =  model_dict["model_config"]["input_shape"]
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

    # tensorflow 2 convert		
	if "classification" in args.config:
		from convert_cls import convert_cls
		convert_cls(input_model, output_dir, INTEL_CONVERT_PATH,
							model_name, export_dir, project_name, model_dict, args.config, shape)

	elif "yolo" in args.config:
		from convert_yolo import convert_yolo
		convert_yolo(input_model, output_dir, INTEL_CONVERT_PATH,
                    		export_dir, project_name, model_dict, args.config, shape)

	# Computing time
	end = time.time()
	logging.info("Converting total time:{}".format(end - start))

if __name__ == '__main__':
    config_logger('./convert.log', 'a', "info")
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', help = "The path of model config")
    args = parser.parse_args()
    sys.exit(main(args) or 0)
