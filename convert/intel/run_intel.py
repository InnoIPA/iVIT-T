import sys, argparse, sys
# Append to API
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[2]/"common"))
from logger import config_logger
from utils import cmd

CONTAINER_NAME = "intel-convert"

def main(args):
    SPLIT_ACTION = False
    command = "./convert/intel/run.sh"
    cmd(command, SPLIT_ACTION)
    command = "docker exec -it {} \
                bash -c 'pip install colorlog && \
                python3 ./convert/intel/convert_intel.py -c {}' ".format(CONTAINER_NAME, args.config)
    cmd(command, SPLIT_ACTION)
    command = "docker stop {}".format(CONTAINER_NAME)
    cmd(command, SPLIT_ACTION)

if __name__ == '__main__':
    config_logger('./convert.log', 'a', "info")
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', help = "The path of model config")
    args = parser.parse_args()
    sys.exit(main(args) or 0)