import sys, os
# Append to API
from ..common import MAIN_PATH
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[2]/"common"))
from logger import config_logger
from utils import cmd

CONTAINER_NAME = "vitis-ai-ivit-t"

def running_xilinx(config:str):
    config_logger('./convert.log', 'a', "info")
    SPLIT_ACTION = False
    command = "{} c".format( os.path.join(MAIN_PATH, "xilinx/Vitis-AI/vitis-ai-start.sh") )
    cmd(command, SPLIT_ACTION)
    command = "docker exec -i {} \
                bash -c 'source /opt/vitis_ai/conda/bin/activate vitis-ai-tensorflow && \
                pip install colorlog && \
                python3 {} -c {}'".format(CONTAINER_NAME, os.path.join(MAIN_PATH, "xilinx/convert_xilinx.py"), config)
    cmd(command, SPLIT_ACTION)
    command = "docker stop {} && docker rm {}".format(CONTAINER_NAME, CONTAINER_NAME)
    cmd(command, SPLIT_ACTION)