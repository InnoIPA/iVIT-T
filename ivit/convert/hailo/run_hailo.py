import sys, os, shutil
# Append to API
from pathlib import Path
from ..common import MAIN_PATH
sys.path.append(str(Path(__file__).resolve().parents[2]/"common"))
from logger import config_logger
from utils import cmd


CONTAINER_NAME = "hailo_ivit_convert"

def running_hailo(config:str):
    config_logger('./convert.log', 'a', "info")
    SPLIT_ACTION = False
    command = os.path.join(MAIN_PATH, "hailo/hailo_sw_suite_docker_run.sh")
    cmd(command, SPLIT_ACTION)
    command = "docker exec -it {} \
                bash -c 'pip install colorlog keras_preprocessing keras_applications && \
                chmod 777 -R /local/workspace/hailo_virtualenv/bin/ && \
                source /local/workspace/hailo_virtualenv/bin/activate && \
                python3 {} -c {}' ".format(CONTAINER_NAME, os.path.join(MAIN_PATH, "hailo/convert_hailo.py"), config)
    cmd(command, SPLIT_ACTION)
    command = "docker stop {}".format(CONTAINER_NAME)
    cmd(command, SPLIT_ACTION)
    
    # Clear generate file
    remove_list = ["hailo_sdk.core.log", "hailo_sdk.client.log", 
                    "hailort.log", "acceleras.log", "allocator.log", 
                    ".bias_correction", ".install_logs", ".stats_collection", "adaround"]
    for key in remove_list:
        if os.path.isdir(key):
            shutil.rmtree(key)
        elif os.path.isfile(key):
            os.remove(key)