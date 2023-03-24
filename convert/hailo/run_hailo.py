import sys, os
from argparse import ArgumentParser, SUPPRESS
# Append to API
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[2]/"common"))
from logger import config_logger
from utils import cmd

CONTAINER_NAME = "hailo_ivit_convert"

def build_argparser():
    parser = ArgumentParser(add_help=False)
    args = parser.add_argument_group('Options')
    args.add_argument('-h', '--help', action='help', default=SUPPRESS, help='Show this help message and exit.')
    args.add_argument('-c', '--config', required=True, help = "The path of model config")
    return parser

def main(args):
    SPLIT_ACTION = False
    command = "./convert/hailo/hailo_sw_suite_docker_run.sh"
    cmd(command, SPLIT_ACTION)
    command = "docker exec -it {} \
                bash -c 'pip install colorlog keras_preprocessing keras_applications && \
                chmod 777 -R /local/workspace/hailo_virtualenv/bin/ && \
                source /local/workspace/hailo_virtualenv/bin/activate && \
                python3 ./convert/hailo/convert_hailo.py -c {}' ".format(CONTAINER_NAME, args.config)
    cmd(command, SPLIT_ACTION)
    command = "docker stop {}".format(CONTAINER_NAME)
    cmd(command, SPLIT_ACTION)
    
    # Clear generate file
    remove_list = ["hailo_sdk.core.log", "hailo_sdk.client.log", 
                    "hailort.log", "acceleras.log", "allocator.log", 
                        ".bias_correction", ".install_logs", ".stats_collection"]
    for key in remove_list:
        if os.path.isdir(key):
            os.rmdir(key)
        elif os.path.isfile(key):
            os.remove(key)

if __name__ == '__main__':
    config_logger('./convert.log', 'a', "info")
    args = build_argparser().parse_args()
    sys.exit(main(args) or 0)