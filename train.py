
import json
import sys
import subprocess
import logging
from common.logger import config_logger

def read_json(path):
    with open(path) as f:
        return json.load(f)

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
    use_model = read_json("./Project/samples/Config.json")
    if 'classification' in use_model['model_json']:
        logging.info('Start training of classification...')
        command = "python3 Classification/classification.py"
        # Run command
        cmd(command)

    elif 'yolo' in use_model['model_json']:
        logging.info('Start training of yolo...')
        command = "python3 ObjectDetection/YOLO/yolo.py"
        # Run command
        cmd(command)

    elif 'unet' in use_model['model_json']:
        logging.info('Start training of unet...')
        pass
    elif 'vae' in use_model['model_json']:
        logging.info('Start training of vae...')
        pass
    else:
        logging.info('The name of json is wrong...')

if __name__ == '__main__':
    config_logger('./training.log', 'w', "info")
    sys.exit(main() or 0)