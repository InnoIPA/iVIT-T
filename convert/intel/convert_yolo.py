import logging, os, shutil, sys, yaml

# Append to API
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]/""))
sys.path.append(str(Path(__file__).resolve().parents[3]/"common"))
from utils import cmd, read_json, write_json, ROOT
from common.check import check_model

def convert_yolo(input_model:str, output_dir:str, convert_path:str,
                    export_dir:str, project_name:str, model_dict:dict, cfg_path:str, shape:list):

    h,w,c = shape
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
    logging.info("Step:1/4,")
    os.chdir(os.path.abspath(os.path.expanduser(convert_path+"/tools/model_downloader")))
    command = "python3 downloader.py --name {} -o {}".format(arch, ROOT + output_dir.split('project/')[-1])
    cmd(command)

    # Copy model in folder
    logging.info('Copy model/cfg to folder')
    logging.info("Step:2/4,")
    os.chdir(os.path.abspath(os.path.expanduser("/workspace")))
    command = "cp {} {}".format(input_model, output_dir + "/public/{}/{}".format(arch, convert_model_name))
    cmd(command)
    command = "cp {} {}".format(cfgpath, output_dir + "/public/{}/keras-YOLOv3-model-set/cfg/{}".format(arch, cfg_name))
    cmd(command)

    # Modify yml input_shape
    yaml_file = convert_path+'/open_model_zoo/models/public/{}/model.yml'.format(arch)
    logging.info(yaml_file)
    with open(yaml_file, 'r') as f:
        data = yaml.load(f)

    data['model_optimizer_args'][0] = '--input_shape=[1,{},{},{}]'.format(h,w,c)
    with open(yaml_file, 'w') as f:
        yaml.dump(data, f)

    # Convert
    logging.info('Start Convert...')
    logging.info("Step:3/4,")
    os.chdir(os.path.abspath(os.path.expanduser(convert_path+"/open_model_zoo/tools/downloader")))
    command = "python3 converter.py -d {} --name {} --precisions FP16".format( ROOT + output_dir.split('project/')[-1], arch)
    cmd(command)

    # Check model is exist
    os.chdir(os.path.abspath(os.path.expanduser("/workspace")))
    check_model(output_dir+"/public/"+arch+"/FP16/"+arch+".bin", ".bin")

    # export bin/mapping/xml
    logging.info("Step:4/4,")
    logging.info("Export model")
    shutil.copyfile(output_dir+"/public/"+arch+"/FP16/"+arch+".bin", export_dir+"/"+project_name+".bin")
    shutil.copyfile(output_dir+"/public/"+arch+"/FP16/"+arch+".mapping", export_dir+"/"+project_name+".mapping")
    shutil.copyfile(output_dir+"/public/"+arch+"/FP16/"+arch+".xml", export_dir+"/"+project_name+".xml")
    # export classes.txt
    shutil.copyfile(model_dict["train_config"]["label_path"], export_dir+'/classes.txt')
    # export yolo.json
    shutil.copyfile(cfg_path, export_dir+'/yolo.json')

    # Added anchors in json
    logging.info("Added anchor in the Config...")
    f = open(cfgpath)
    text = f.read()
    logging.info(text.split("anchors")[-1].split("\nclasses")[0].split("=")[-1])
    anchor = text.split("anchors")[-1].split("\nclasses")[0].split("=")[-1]
    f.close()
    orignal = read_json(export_dir+'/yolo.json')
    orignal["anchors"] = anchor
    write_json(export_dir+'/yolo.json', orignal)