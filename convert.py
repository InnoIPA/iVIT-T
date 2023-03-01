import sys, subprocess, logging, argparse
from common.logger import config_logger
from common.utils import read_json 

def cmd(command):
    process = subprocess.Popen(command.split(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT,shell=False)
    logging.info("PID:{},".format(process.pid))
    for line in iter(process.stdout.readline,b''):
        line = line.rstrip().decode()
        if line.isspace(): 
            continue
        else:
            print(line)
        
def main(args):
    # Read model_json
    model_dict = read_json(args.config)
    # Catch platform
    platform = model_dict["export_platform"]

    if platform == "nvidia":
        logging.info('Convert the model to use the model of nvidia device')
        command = "python3 convert/nvidia/convert_nvidia.py -c {}".format(args.config)
        # Run command
        cmd(command)

    elif platform == "intel":
        logging.info('Convert the model to use the model of intel device')
        command = "python3 convert/intel/run_intel.py -c {}".format(args.config) 
        # Run command
        cmd(command)

    elif platform == "xilinx":
        logging.info('Convert the model to use the model of xilinx device')
        command = "python3 convert/xilinx/run_xilinx.py -c {}".format(args.config)
        # Run command
        cmd(command)

    elif platform == "hailo":
        logging.info('Convert the model to use the model of hailo device')
        command = "python3 convert/hailo/run_hailo.py -c {}".format(args.config)
        # Run command
        cmd(command)

    logging.info('Converted.')

if __name__ == '__main__':
    config_logger('./convert.log', 'w', "info")
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', help = "The path of model config")
    args = parser.parse_args()
    sys.exit(main(args) or 0)