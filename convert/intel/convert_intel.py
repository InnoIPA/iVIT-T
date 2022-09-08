import sys, os
import subprocess, shutil
import logging
import yaml
# Append to API
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[2]/"common"))
from logger import config_logger
from utils import read_json, write_json

INTEL_VERSION = "openvino_2021.4.752"
INTEL_CONVERT_PATH = "/opt/intel/{}/deployment_tools".format(INTEL_VERSION)

def cmd(command):
	logging.info(command.split())
	process = subprocess.Popen(command.split(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=False)
	for line in iter(process.stdout.readline,b''):
		line = line.rstrip().decode()
		if line.isspace(): 
			continue
		else:
			# print(line)
			logging.info(line)
        # if not subprocess.Popen.poll(process) is None:
        #     process.returncode
        #     break

def main():
	# Read Config.json
	dict = read_json("Project/samples/Config.json")
	# Read model_json
	model_dict = read_json(dict["model_json"])
	model_list = os.listdir(model_dict["train_config"]["save_model_path"])
	model_name = [best for best in model_list if "best" in best][0]
	input_model = model_dict["train_config"]["save_model_path"] +'/'+ model_name
	output_dir = model_dict["train_config"]["save_model_path"]+'/intel_model'
	export_dir = model_dict["train_config"]["save_model_path"].split("weights")[0]+'export'
	h,w,c =  model_dict["model_config"]["input_shape"]
	project_name = dict["model_json"].split("/")[2]

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
	if "classification" in dict['model_json']:
		logging.info('Start keras2tensorflow...')
		output_model = input_model.split('.h5')[0]+".pb"
		output_model = output_dir +"/"+ input_model.split('weights/')[-1].split('.h5')[0]+".pb"
		split_output_model = output_model.split('.')
		# keras2tensorflow
		command = "python3 convert/common/keras2tensorflow.py --input_model {} --output_model {}".format(input_model, output_model)
		cmd(command)
		
		# tensorflow2IR
		logging.info('Start tensorflow2IR...')
		os.chdir(os.path.abspath(os.path.expanduser(INTEL_CONVERT_PATH+"/model_optimizer")))
		command = "python3 mo_tf.py --input_model {} --output_dir {} --input_shape [1,{},{},{}] --disable_nhwc_to_nchw".format('/workspace'+ split_output_model[-2]+ '.' + split_output_model[-1], 
																																'/workspace'+ output_dir.split(".")[-1],
																																c,h,w)
		cmd(command)

		#export bin/mapping/xml
		logging.info("export model")
		os.chdir(os.path.abspath(os.path.expanduser("/workspace")))
		m_name = model_name.split(".")[0]
		shutil.copyfile(output_dir+"/"+m_name+".bin", export_dir+"/"+project_name+".bin")
		shutil.copyfile(output_dir+"/"+m_name+".mapping", export_dir+"/"+project_name+".mapping")
		shutil.copyfile(output_dir+"/"+m_name+".xml", export_dir+"/"+project_name+".xml")
		#export classes.txt
		shutil.copyfile(model_dict["train_config"]["label_path"], export_dir+'/classes.txt')
		#export classification.json
		shutil.copyfile(dict["model_json"], export_dir+'/classification.json')

	elif "yolo" in dict['model_json']:

		arch = model_dict["model_config"]["arch"]
		cfgpath = model_dict["train_config"]["save_model_path"].split("weight")[0]+arch+".cfg"
		
		# Change name for intel model
		if "tiny" in arch:
			arch = "yolo-v4-tiny-tf"
			convert_model_name = "yolov4-tiny.weights"
			cfg_name = "yolov4-tiny.cfg"
		else:
			arch = "yolo-v4-tf"
			convert_model_name = "yolov4.weights"
			cfg_name = "yolov4.cfg"

		# Download public yolov4/yolov4-tiny folder
		logging.info('Start download public model...')
		os.chdir(os.path.abspath(os.path.expanduser(INTEL_CONVERT_PATH+"/tools/model_downloader")))
		command = "python3 downloader.py --name {} -o {}".format(arch, '/workspace'+ output_dir.split('.')[-1])
		cmd(command)

		# Copy model in folder
		logging.info('copy model/cfg to folder')
		os.chdir(os.path.abspath(os.path.expanduser("/workspace")))
		command = "cp {} {}".format(input_model, output_dir + "/public/{}/{}".format(arch, convert_model_name))
		cmd(command)
		command = "cp {} {}".format(cfgpath, output_dir + "/public/{}/keras-YOLOv3-model-set/cfg/{}".format(arch, cfg_name))
		cmd(command)

		# Modify yml input_shape
		yaml_file = INTEL_CONVERT_PATH+'/open_model_zoo/models/public/{}/model.yml'.format(arch)
		logging.info(yaml_file)
		with open(yaml_file, 'r') as f:
			data = yaml.load(f)

		data['model_optimizer_args'][0] = '--input_shape=[1,{},{},{}]'.format(h,w,c)
		with open(yaml_file, 'w') as f:
			yaml.dump(data, f)

		# Convert
		logging.info('Start Convert...')
		os.chdir(os.path.abspath(os.path.expanduser(INTEL_CONVERT_PATH+"/open_model_zoo/tools/downloader")))
		command = "python3 converter.py -d {} --name {} --precisions FP16".format( '/workspace'+ output_dir.split('.')[-1], arch)
		cmd(command)

		# export bin/mapping/xml
		logging.info("export model")
		os.chdir(os.path.abspath(os.path.expanduser("/workspace")))
		shutil.copyfile(output_dir+"/public/"+arch+"/FP16/"+arch+".bin", export_dir+"/"+project_name+".bin")
		shutil.copyfile(output_dir+"/public/"+arch+"/FP16/"+arch+".mapping", export_dir+"/"+project_name+".mapping")
		shutil.copyfile(output_dir+"/public/"+arch+"/FP16/"+arch+".xml", export_dir+"/"+project_name+".xml")
		# export classes.txt
		shutil.copyfile(model_dict["train_config"]["label_path"], export_dir+'/classes.txt')
		# export classification.json
		shutil.copyfile(dict["model_json"], export_dir+'/yolo.json')

		# Added anchors in json
		logging.info("Add anchors in model.json")
		f = open(cfgpath)
		text = f.read()
		logging.info(text.split("anchors")[-1].split("\nclasses")[0].split("=")[-1])
		anchor = text.split("anchors")[-1].split("\nclasses")[0].split("=")[-1]
		f.close()
		orignal = read_json(export_dir+'/yolo.json')
		orignal["anchors"] = anchor
		write_json(export_dir+'/yolo.json', orignal)

if __name__ == '__main__':
    config_logger('./convert.log', 'a', "info")
    sys.exit(main() or 0)


