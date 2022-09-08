import sys, os
import logging
import subprocess
# Append to API
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]/"common"))
sys.path.append(str(Path(__file__).resolve().parents[1]))
from setting import Setting
from ImportParameter import Parameter
from logger import config_logger
from utils import read_json, write_json
from metrics import test_summary, metrics_report

def cmd(command):
    process = subprocess.Popen(command.split(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT,shell=False)
    for line in iter(process.stdout.readline,b''):
        line = line.rstrip().decode()
        if line.isspace(): 
            continue
        else:
            logging.info(line)

        # if not subprocess.Popen.poll(process) is None:
        #     process.returncode
        #     break

def main():
    # Instantiation
    Init_set = Setting()

    # Get model relative info
    logging.info("Loading config")
    Dict = read_json(read_json("./Project/samples/Config.json")['model_json'])
    Init_set.checkpath(Dict)

    # Parameter import config
    Parm = Parameter(Dict)
    # Parm.json_to_name()
    Parm.json_to_data()
    Parm.json_to_cfg()

    # Training subprocess
    logging.info('Training...')
    path_list = Dict['train_config']['train_dataset_path'].split('/')
    parampath = path_list[0]+'/'+path_list[1]+"/"+path_list[2]+"/"+path_list[3]
    command = "ObjectDetection/YOLO/darknet/darknet detector train {} {} {} -dont_show -mjpeg_port {} -map -gpus {}".format(parampath + '/Training.data',
                                                                                                                            parampath+'/'+ Dict['model_config']['arch']+'.cfg',
                                                                                                                            Dict['train_config']['pretrained_model_path'], 
                                                                                                                            8090,
                                                                                                                            Dict['train_config']['GPU'])    
    # # Run command
    cmd(command)

    # Metrics
    logging.info("Metrics...")
    model_name = [name for name in os.listdir(Dict['train_config']['save_model_path']) if "best" in name]
    if len(model_name)!=0:
        predict_info, truth_info = test_summary(Dict, 
                                    parampath+'/'+ Dict['model_config']['arch']+'.cfg', 
                                    parampath + '/Training.data', 
                                    Dict['train_config']['save_model_path']+'/'+model_name[0])
        value = metrics_report(predict_info, truth_info)
        metrics_dic = { "percision":round(value[0],2),
                        "recall":round(value[1],2),  
                        "mAP":round(value[2],2)}

        logging.info(metrics_dic)
        # delete old metrics
        if os.path.isfile(Dict['train_config']['save_model_path']+'/'+'metrics.json'):
            os.remove(Dict['train_config']['save_model_path']+'/'+'metrics.json')
        write_json(Dict['train_config']['save_model_path']+'/'+'metrics.json', metrics_dic)
    
    logging.info("Ending...")

if __name__ == '__main__':
    config_logger('./training.log', 'a', "info")
    sys.exit(main() or 0)