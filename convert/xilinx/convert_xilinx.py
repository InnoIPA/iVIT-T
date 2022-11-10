import sys, os
import subprocess, shutil
import logging
import yaml
# Append to API
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[2]/"common"))
from logger import config_logger
from utils import read_json, write_json

def cmd(command):
	logging.info(command.split())
	process = subprocess.Popen(command.split(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT,shell=False)
	for line in iter(process.stdout.readline,b''):
		line = line.rstrip().decode()
		if line.isspace(): 
			continue
		else:
			print(line)

def main():
    # Read Config.json
    dict = read_json("Project/samples/Config.json")
    # Read model_json
    model_dict = read_json(dict["model_json"])
    model_list = os.listdir(model_dict["train_config"]["save_model_path"])
    model_name = [best for best in model_list if "best" in best][0]
    input_model = model_dict["train_config"]["save_model_path"] +'/'+ model_name
    output_dir = model_dict["train_config"]["save_model_path"]+'/xilinx_model'
    export_dir = model_dict["train_config"]["save_model_path"].split("weights")[0]+'export'
    h,w,c =  model_dict["model_config"]["input_shape"]
    shape = "{},{},{}".format(h,w,c)
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
        output_model = output_dir +"/"+ input_model.split('weights/')[-1].split('.h5')[0]+".pb"
        split_output_model = output_model.split('.')
        train_path = model_dict["train_config"]["train_dataset_path"]
        input_tensor_name = 'input_1'
        output_tensor_name = 'dense_1/Softmax'
        output_txt = "/workspace"+output_dir.split('.')[-1]+"/train.txt"

        # keras2tensorflow
        command = "python3 convert/common/keras2tensorflow.py --input_model {} --output_model {}".format(input_model, output_model)
        cmd(command)

        # generate train.txt
        command = "python3 convert/xilinx/Vitis-AI/vitis-ai-utility/model2xmodel_package/common/generate_image_path.py -img_dir_path {} -save_path {}".format(train_path, output_txt)
        cmd(command)

        # change path
        XILINX_CONVERT_PATH = "./convert/xilinx/Vitis-AI/vitis-ai-utility/model2xmodel_package/common"
        os.chdir(os.path.abspath(os.path.expanduser(XILINX_CONVERT_PATH)))

        # quantize pb
        command = "./quantize_model.sh -is {} -i {} -in {} -on {} -o {} -tp {}".format(shape, 
                                                                                        '/workspace'+ split_output_model[-2]+ '.' + split_output_model[-1],
                                                                                        input_tensor_name,
                                                                                        output_tensor_name,
                                                                                        "/workspace"+output_dir.split('.')[-1],
                                                                                        output_txt)
        cmd(command)
        
        # convert xmodel
        command = "vai_c_tensorflow --frozen_pb {} --arch {} --output_dir {} --net_name {} --options {}".format("/workspace"+output_dir.split('.')[-1]+"/quantize_eval_model.pb",
                                                                                                                "k26_arch.json",
                                                                                                                "/workspace"+output_dir.split('.')[-1],
                                                                                                                project_name,
                                                                                                                "{'mode':'normal','save_kernel':'','input_shape':"+"'{},{},{},{}'".format(1,w,h,c)+"}")
        cmd(command)

        #export xmodel
        logging.info("export model")
        shutil.copyfile("/workspace"+output_dir.split('.')[-1]+"/"+project_name+".xmodel", 
                            "/workspace"+export_dir.split('.')[-1]+"/"+project_name+".xmodel")
        #export classes.txt
        shutil.copyfile("/workspace"+model_dict["train_config"]["label_path"].split('.')[1]+ ".txt", 
                                "/workspace"+export_dir.split('.')[-1]+'/classes.txt')
        #export classification.json
        shutil.copyfile("/workspace"+dict["model_json"].split('.')[1]+".json", 
                                "/workspace"+export_dir.split('.')[-1]+'/classification.json')

    elif "yolo" in dict['model_json']:
        arch = model_dict["model_config"]["arch"]
        cfgpath = model_dict["train_config"]["save_model_path"].split("weight")[0]+arch+".cfg"
        output_h5 = output_dir +"/"+ input_model.split('weights/')[-1].split('.weights')[0]+".h5"
        output_pb = output_dir +"/"+ input_model.split('weights/')[-1].split('.weights')[0]+".pb"
        split_output_model = output_pb.split('.')
        train_txt = "/workspace"+export_dir.split("export")[0].split('.')[1]+"train.txt"

        input_tensor_name = 'image_input'
        if "tiny" in arch:
            output_tensor_name = 'conv2d_9/BiasAdd,conv2d_12/BiasAdd'
        else:
            output_tensor_name = 'conv2d_93/BiasAdd,conv2d_101/BiasAdd,conv2d_109/BiasAdd'

        # convert weights to h5
        command = "python3 convert/common/darknet2keras.py -f {} {} {}".format(cfgpath, 
                                                                            input_model,
                                                                            output_h5)
        cmd(command)

        # keras2tensorflow
        command = "python3 convert/common/keras2tensorflow.py --input_model {} --output_model {}".format(output_h5, 
                                                                                                            output_pb)
        cmd(command)

        # change path
        XILINX_CONVERT_PATH = "./convert/xilinx/Vitis-AI/vitis-ai-utility/model2xmodel_package/common"
        os.chdir(os.path.abspath(os.path.expanduser(XILINX_CONVERT_PATH)))

        # quantize pb
        command = "./quantize_model.sh -is {} -i {} -in {} -on {} -o {} -tp {}".format(shape, 
                                                                                        '/workspace'+ split_output_model[-2]+ '.' + split_output_model[-1],
                                                                                        input_tensor_name,
                                                                                        output_tensor_name,
                                                                                        "/workspace"+output_dir.split('.')[-1],
                                                                                        train_txt)
        cmd(command)
        
        # convert xmodel
        command = "vai_c_tensorflow --frozen_pb {} --arch {} --output_dir {} --net_name {} --options {}".format("/workspace"+output_dir.split('.')[-1]+"/quantize_eval_model.pb",
                                                                                                                "k26_arch.json",
                                                                                                                "/workspace"+output_dir.split('.')[-1],
                                                                                                                project_name,
                                                                                                                "{'mode':'normal','save_kernel':'','input_shape':"+"'{},{},{},{}'".format(1,w,h,c)+"}")
        cmd(command)

        #export xmodel
        logging.info("export model")
        shutil.copyfile("/workspace"+output_dir.split('.')[-1]+"/"+project_name+".xmodel", 
                                    "/workspace"+export_dir.split('.')[-1]+"/"+project_name+".xmodel")
        #export classes.txt
        shutil.copyfile("/workspace"+model_dict["train_config"]["label_path"].split('.')[1]+ ".txt", 
                                "/workspace"+export_dir.split('.')[-1]+'/classes.txt')
        #export yolo.json
        shutil.copyfile("/workspace"+dict["model_json"].split('.')[1]+".json", 
                        "/workspace"+export_dir.split('.')[-1]+'/yolo.json')

        # Add anchor in json
        logging.info("add anchor in json")
        f = open("/workspace"+cfgpath.split('.')[1]+".cfg")
        text = f.read()
        logging.info(text.split("anchors")[-1].split("\nclasses")[0].split("=")[-1])
        anchor = text.split("anchors")[-1].split("\nclasses")[0].split("=")[-1]
        f.close()
        orignal = read_json("/workspace"+export_dir.split('.')[-1]+'/yolo.json')
        orignal["anchors"] = anchor
        write_json("/workspace"+export_dir.split('.')[-1]+'/yolo.json', orignal)

if __name__ == '__main__':
    config_logger('./convert.log', 'a', "info")
    sys.exit(main() or 0)


