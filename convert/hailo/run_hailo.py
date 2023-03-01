import sys, argparse
# Append to API
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[2]/"common"))
from logger import config_logger
from utils import cmd

CONTAINER_NAME = "hailo_ivit_convert"

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

if __name__ == '__main__':
    config_logger('./convert.log', 'a', "info")
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', help = "The path of model config")
    args = parser.parse_args()
    sys.exit(main(args) or 0)