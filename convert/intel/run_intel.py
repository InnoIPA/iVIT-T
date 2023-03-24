import sys, sys
from argparse import ArgumentParser, SUPPRESS
# Append to API
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[2]/"common"))
from logger import config_logger
from utils import cmd

CONTAINER_NAME = "intel-convert"

def build_argparser():
    parser = ArgumentParser(add_help=False)
    args = parser.add_argument_group('Options')
    args.add_argument('-h', '--help', action='help', default=SUPPRESS, help='Show this help message and exit.')
    args.add_argument('-c', '--config', required=True, help = "The path of model config")
    return parser

def main(args):
    SPLIT_ACTION = False
    command = "./convert/intel/run.sh"
    cmd(command, SPLIT_ACTION)
    command = "docker exec -it {} \
                bash -c 'python3 ./convert/intel/convert_intel.py -c {}' ".format(CONTAINER_NAME, args.config)
    cmd(command, SPLIT_ACTION)
    command = "docker stop {}".format(CONTAINER_NAME)
    cmd(command, SPLIT_ACTION)

if __name__ == '__main__':
    config_logger('./convert.log', 'a', "info")
    args = build_argparser().parse_args()
    sys.exit(main(args) or 0)