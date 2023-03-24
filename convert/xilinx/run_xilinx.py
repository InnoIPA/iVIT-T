import sys
from argparse import ArgumentParser, SUPPRESS
# Append to API
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[2]/"common"))
from logger import config_logger
from utils import cmd

CONTAINER_NAME = "vitis-ai-ivit-t"

def build_argparser():
    parser = ArgumentParser(add_help=False)
    args = parser.add_argument_group('Options')
    args.add_argument('-h', '--help', action='help', default=SUPPRESS, help='Show this help message and exit.')
    args.add_argument('-c', '--config', required=True, help = "The path of model config")
    return parser

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
    args = build_argparser().parse_args()
    sys.exit(main(args) or 0)
