import sys, os
import subprocess, shutil
import logging
# Append to API
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[2]/"common"))
from logger import config_logger
from utils import read_json 


def cmd(command):
    process = subprocess.Popen(command.split(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT,shell=False)
    for line in iter(process.stdout.readline,b''):
        line = line.rstrip().decode()
        if line.isspace(): 
            continue
        else:
            print(line)
        
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
    output_dir = model_dict["train_config"]["save_model_path"]+'/nvidia_model'
    export_dir = model_dict["train_config"]["save_model_path"].split("weights")[0]+'export'
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

    # keras convert	to onnx	
    if "classification" in dict['model_json']:
        logging.info('Start keras2onnx...')
        command = "python3 convert/common/keras2onnx.py --keras_model_file {} --output_file {} --op_set {}".format(input_model
                                                                                                , output_dir+"/"+model_name.split(".")[0]+".onnx"
                                                                                                , 14)

        # Run command
        cmd(command)

        #export .onnx
        logging.info("export model")
        m_name = model_name.split(".")[0]
        shutil.copyfile(output_dir+"/"+m_name+".onnx", export_dir+"/"+project_name+".onnx")
        #export classes.txt
        shutil.copyfile(model_dict["train_config"]["label_path"], export_dir+'/classes.txt')
        #export classification.json
        shutil.copyfile(dict["model_json"], export_dir+'/classification.json')

    elif "yolo" in dict['model_json']:
        arch = model_dict["model_config"]["arch"]
        #export weights
        logging.info("export model")
        shutil.copyfile(input_model, export_dir+"/"+project_name+".weights")
        #export classes.txt
        shutil.copyfile(model_dict["train_config"]["label_path"], export_dir+'/classes.txt')
        #export yolo.cfg
        shutil.copyfile(dict["model_json"].split("yolo.json")[0]+'/'+arch+'.cfg', export_dir+'/'+project_name+'.cfg')
        #export classification.json
        shutil.copyfile(dict["model_json"], export_dir+'/yolo.json')
        # rm null dir
        os.rmdir(output_dir)
        
    logging.info('Converted.')

if __name__ == '__main__':
    config_logger('./convert.log', 'a', "info")
    sys.exit(main() or 0)