import sys, argparse, subprocess
# Append to API
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[2]/"common"))
from logger import config_logger
from utils import cmd

CONTAINER_NAME = "vitis-ai-ivit-t"

def main(args):
    SPLIT_ACTION = False
    command = "./convert/xilinx/Vitis-AI/vitis-ai-start.sh c"
    cmd(command, SPLIT_ACTION)
    command = "docker exec -it {} \
                bash -c 'source /opt/vitis_ai/conda/bin/activate vitis-ai-tensorflow && \
                pip install colorlog && \
                python3 ./convert/xilinx/convert_xilinx.py -c {}' ".format(CONTAINER_NAME, args.config)
    cmd(command, SPLIT_ACTION)
    command = "docker stop {} && docker rm {}".format(CONTAINER_NAME, CONTAINER_NAME)
    cmd(command, SPLIT_ACTION)

if __name__ == '__main__':
    config_logger('./convert.log', 'a', "info")
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', help = "The path of model config")
    args = parser.parse_args()
    sys.exit(main(args) or 0)
