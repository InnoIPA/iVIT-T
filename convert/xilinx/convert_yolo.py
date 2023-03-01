import logging, os, shutil, sys

# Append to API
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]/""))
sys.path.append(str(Path(__file__).resolve().parents[3]/"common"))
from utils import cmd, write_json, read_json, ROOT, read_txt, write_txt
from common.check import check_model

def convert_yolo(input_model:str, output_dir:str, export_dir:str, project_name:str, model_dict:dict, cfg_path:str, shape:list, shape_str:str):

    h, w, c= shape
    arch = model_dict["model_config"]["arch"]
    cfgpath = model_dict["train_config"]["save_model_path"].split("weight")[0]+arch+".cfg"
    output_h5 = output_dir +"/"+ input_model.split('weights/')[-1].split('.weights')[0]+".h5"
    output_pb = output_dir +"/"+ input_model.split('weights/')[-1].split('.weights')[0]+".pb"
    split_output_model = output_pb.split('project/')
    train_txt = "/workspace"+export_dir.split("export")[0].split('.')[1]+"train.txt"
    train_txt = data_process(train_txt)

    input_tensor_name = 'image_input'
    if "tiny" in arch:
        output_tensor_name = 'conv2d_9/BiasAdd,conv2d_12/BiasAdd'
    else:
        output_tensor_name = 'conv2d_93/BiasAdd,conv2d_101/BiasAdd,conv2d_109/BiasAdd'

    # convert weights to h5
    logging.info("Convert Darknet to Keras...")
    logging.info("Step:1/5,")
    command = "python3 convert/common/darknet2keras.py -f {} {} {}".format(cfgpath, 
                                                                        input_model,
                                                                        output_h5)
    cmd(command)

    # Check model is exist
    check_model(output_h5, ".h5")

    # keras2tensorflow
    logging.info("Convert Keras to Tensorflow...")
    logging.info("Step:2/5,")
    command = "python3 convert/common/keras2tensorflow.py --input_model {} --output_model {}".format(output_h5, 
                                                                                                        output_pb)
    cmd(command)

    # Check model is exist
    check_model(output_pb, ".pb")

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
                                                                                    ROOT + output_dir.split('project/')[-1],
                                                                                    train_txt)
    cmd(command)

    # Check model is exist
    check_model( ROOT +output_dir.split('project/')[-1]+"/quantize_eval_model.pb", "quantize.pb")
    
    # convert xmodel
    logging.info("Step:4/5,")
    logging.info("Convert model to Xilnix...")
    command = "vai_c_tensorflow --frozen_pb {} --arch {} --output_dir {} --net_name {} --options {}".format(ROOT +output_dir.split('project/')[-1]+"/quantize_eval_model.pb",
                                                                                                            "k26_arch.json",
                                                                                                            ROOT +output_dir.split('project/')[-1],
                                                                                                            project_name,
                                                                                                            "{'mode':'normal','save_kernel':'','input_shape':"+"'{},{},{},{}'".format(1,w,h,c)+"}")
    cmd(command)

    # Check model is exist
    check_model(ROOT +output_dir.split('project/')[-1]+"/"+project_name+".xmodel", ".xmodel")

    #export xmodel
    logging.info("Step:5/5,")
    logging.info("Export model")
    shutil.copyfile(ROOT+output_dir.split('project/')[-1]+"/"+project_name+".xmodel", 
                                ROOT+export_dir.split('project/')[-1]+"/"+project_name+".xmodel")
    #export classes.txt
    shutil.copyfile(ROOT + model_dict["train_config"]["label_path"].split('project/')[-1], 
                            ROOT+export_dir.split('project/')[-1]+'/classes.txt')
    #export yolo.json
    shutil.copyfile(ROOT+cfg_path.split('project/')[-1], 
                    ROOT+export_dir.split('project/')[-1]+'/yolo.json')

    # Add anchor in json
    logging.info("Added anchor in the Config...")
    f = open(ROOT+cfgpath.split('project/')[-1])

    text = f.read()
    logging.info(text.split("anchors")[-1].split("\nclasses")[0].split("=")[-1])
    anchor = text.split("anchors")[-1].split("\nclasses")[0].split("=")[-1]
    f.close()
    orignal = read_json(ROOT +export_dir.split('project/')[-1]+'/yolo.json')
    orignal["anchors"] = anchor
    write_json(ROOT +export_dir.split('project/')[-1]+'/yolo.json', orignal)

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
    