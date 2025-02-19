import logging, os, shutil, sys

# Append to API
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]/""))
from common import MAIN_PATH, check_model
sys.path.append(str(Path(__file__).resolve().parents[3]/"common"))
from utils import cmd, write_json, read_json, ROOT, read_txt, write_txt

def convert_unet(input_model:str, output_dir:str, export_dir:str, project_name:str, model_dict:dict, cfg_path:str, shape:list, shape_str:str):

    h, w, c = shape
    logging.info('Start converting...')
    ckpt_model = output_dir +"/"+ input_model.split('weights/')[-1].split('.h5')[0]+".ckpt"
    output_model = output_dir +"/"+ input_model.split('weights/')[-1].split('.h5')[0]+".pb"
    split_output_model = output_model.split('project/')
    train_path = model_dict["train_config"]["train_dataset_path"]
    input_tensor_name = 'input_1'
    output_tensor_name = 'final_conv/BiasAdd'
    output_txt = ROOT + output_dir.split('project/')[-1]+"/train.txt"

    # keras2tensorflow
    logging.info("Convert Keras to Tensorflow...")
    logging.info("Step:1/6,")
    command = "python3 {}/common/keras2ckpt.py -m {} -o {}".format(MAIN_PATH, input_model, ckpt_model)
    logging.error(ckpt_model)
    cmd(command)

    logging.info("Freezing model...")
    logging.info("Step:2/6,")
    command = "freeze_graph --input_meta_graph {}.meta \
                --input_checkpoint {} --input_binary true \
                --output_graph {}  --output_node_names {}".format(ckpt_model, ckpt_model, output_model, output_tensor_name)
    cmd(command)

    # Check model is exist
    status = check_model(output_model, ".pb")
    if not status:
        return False
    
    # Generate train.txt
    logging.info("Generate train.txt:{}".format(output_txt))
    logging.info("Step:3/6,")
    command = "python3 {}/xilinx/Vitis-AI/vitis-ai-utility/model2xmodel_package/common/generate_image_path.py \
                        -img_dir_path {} -save_path {} -length {}".format(MAIN_PATH, os.path.join(train_path, "images"), output_txt, 30)
    cmd(command)
    output_txt = data_process(output_txt)

    # change path
    XILINX_CONVERT_PATH = "{}/xilinx/Vitis-AI/vitis-ai-utility/model2xmodel_package/common".format(MAIN_PATH)
    os.chdir(os.path.abspath(os.path.expanduser(XILINX_CONVERT_PATH)))

    # quantize pb
    logging.info("Quentize model...")
    logging.info("Step:4/6,")
    command = "./quantize_model.sh -is {} -i {} -in {} -on {} -o {} -tp {} -pre {} \
                        ".format(   
                                    shape_str, 
                                    ROOT + split_output_model[-1],
                                    input_tensor_name,
                                    output_tensor_name,
                                    ROOT +output_dir.split('project/')[-1],
                                    output_txt,
                                    "int8"
                                )
    cmd(command)
    
    # convert xmodel
    logging.info("Convert model to Xilnix...")
    logging.info("Step:5/6,")
    command = "vai_c_tensorflow --frozen_pb {} --arch {} --output_dir {} --net_name {} --options {}".format(ROOT +output_dir.split('project/')[-1]+"/quantize_eval_model.pb",
                                                                                                            "k26_arch.json",
                                                                                                            ROOT +output_dir.split('project/')[-1],
                                                                                                            project_name,
                                                                                                            "{'mode':'normal','save_kernel':'','input_shape':"+"'{},{},{},{}'".format(1,h,w,c)+"}")
    cmd(command)

    # Check model is exist
    status = check_model(ROOT +output_dir.split('project/')[-1]+"/"+project_name+".xmodel", ".xmodel")
    if not status:
        return False
    
    #export xmodel
    logging.info("Step:6/6,")
    logging.info("Export model")
    shutil.copyfile(ROOT + output_dir.split('project/')[-1]+"/"+project_name+".xmodel", 
                        ROOT +export_dir.split('project/')[-1]+"/"+project_name+".xmodel")
    #export classes.txt
    shutil.copyfile(ROOT +model_dict["train_config"]["label_path"].split('project/')[-1], 
                            ROOT +export_dir.split('project/')[-1]+'/classes.txt')
    #export classification.json
    shutil.copyfile(ROOT+cfg_path.split('project/')[-1], 
                            ROOT+export_dir.split('project/')[-1]+'/classification.json')
    
def data_process(path:str):
    length = 30
    new_path = os.path.split(path)[0] + '/train_xilinx.txt'
    content = [val for val in read_txt(path).split("\n") if val !=""]
    if len(content) > length:
        content = content[:length+1]
        for val in content:
            write_txt(new_path, str(val))
        return new_path
    else:
        return path