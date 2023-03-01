import logging, os, shutil, sys

# Append to API
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]/""))
sys.path.append(str(Path(__file__).resolve().parents[3]/"common"))
from utils import cmd, ROOT
from common.check import check_model

def convert_cls(input_model:str, output_dir:str, export_dir:str, project_name:str, model_dict:dict, cfg_path:str, shape:list, shape_str:str):

    h, w, c = shape
    logging.info('Start converting...')
    output_model = output_dir +"/"+ input_model.split('weights/')[-1].split('.h5')[0]+".pb"
    split_output_model = output_model.split('project/')
    train_path = model_dict["train_config"]["train_dataset_path"]
    input_tensor_name = 'input_1'
    output_tensor_name = 'dense_1/Softmax'
    output_txt = ROOT + output_dir.split('project/')[-1]+"/train.txt"

    # keras2tensorflow
    logging.info("Convert Keras to Tensorflow...")
    logging.info("Step:1/5,")
    command = "python3 convert/common/keras2tensorflow.py --input_model {} --output_model {}".format(input_model, output_model)
    cmd(command)

    # Check model is exist
    check_model(output_model, ".pb")

    # Generate train.txt
    logging.info("Generate train.txt:{}".format(output_txt))
    logging.info("Step:2/5,")
    command = "python3 convert/xilinx/Vitis-AI/vitis-ai-utility/model2xmodel_package/common/generate_image_path.py -img_dir_path {} -save_path {} -length {}".format(train_path, output_txt, 30)
    cmd(command)

    # change path
    XILINX_CONVERT_PATH = "./convert/xilinx/Vitis-AI/vitis-ai-utility/model2xmodel_package/common"
    os.chdir(os.path.abspath(os.path.expanduser(XILINX_CONVERT_PATH)))

    # quantize pb
    logging.info("Quentize model...")
    logging.info("Step:3/5,")
    command = "./quantize_model.sh -is {} -i {} -in {} -on {} -o {} -tp {}".format(shape_str, 
                                                                                    ROOT + split_output_model[-1],
                                                                                    input_tensor_name,
                                                                                    output_tensor_name,
                                                                                    ROOT +output_dir.split('project/')[-1],
                                                                                    output_txt)
    cmd(command)
    
    # convert xmodel
    logging.info("Convert model to Xilnix...")
    logging.info("Step:4/5,")
    command = "vai_c_tensorflow --frozen_pb {} --arch {} --output_dir {} --net_name {} --options {}".format(ROOT +output_dir.split('project/')[-1]+"/quantize_eval_model.pb",
                                                                                                            "k26_arch.json",
                                                                                                            ROOT +output_dir.split('project/')[-1],
                                                                                                            project_name,
                                                                                                            "{'mode':'normal','save_kernel':'','input_shape':"+"'{},{},{},{}'".format(1,h,w,c)+"}")
    cmd(command)

    # Check model is exist
    check_model(ROOT +output_dir.split('project/')[-1]+"/"+project_name+".xmodel", ".xmodel")

    #export xmodel
    logging.info("Step:5/5,")
    logging.info("Export model")
    shutil.copyfile(ROOT + output_dir.split('project/')[-1]+"/"+project_name+".xmodel", 
                        ROOT +export_dir.split('project/')[-1]+"/"+project_name+".xmodel")
    #export classes.txt
    shutil.copyfile(ROOT +model_dict["train_config"]["label_path"].split('project/')[-1], 
                            ROOT +export_dir.split('project/')[-1]+'/classes.txt')
    #export classification.json
    shutil.copyfile(ROOT+cfg_path.split('project/')[-1], 
                            ROOT+export_dir.split('project/')[-1]+'/classification.json')