import json
import sys, os
import subprocess
import logging
from common.logger import config_logger
from common.utils import read_json 

def cmd(command):
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
    # Catch platform
    platform = model_dict["export_platform"]

    if platform == "nvidia":
        logging.info('Convert the model to use the model of nvidia device')
        command = "python3 convert/nvidia/convert_nvidia.py"
        # Run command
        cmd(command)

    elif platform == "intel":
        logging.info('Convert the model to use the model of intel device')
        command = "./convert/intel/run_intel.sh" 
        # Run command
        cmd(command)

    elif platform == "xilinx":
        logging.info('Convert the model to use the model of xilinx device')
        command = "python3 convert/xilinx/run_xilinx.py" 
        # Run command
        cmd(command)
        logging.info('Converted.')

if __name__ == '__main__':
    config_logger('./convert.log', 'w', "info")
    sys.exit(main() or 0)