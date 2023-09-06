# Copyright (c) 2023 Innodisk Corporation
# 
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

import sys, os
# Append to API
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]/""))
from common import MAIN_PATH
sys.path.append(str(Path(__file__).resolve().parents[2]/"common"))
from logger import config_logger
from utils import cmd

CONTAINER_NAME = "intel-convert"

def running_intel(config:str):
    config_logger('./convert.log', 'a', "info")
    SPLIT_ACTION = False
    command = os.path.join(MAIN_PATH, "intel/run.sh")
    cmd(command, SPLIT_ACTION)
    command = "docker exec -it {} \
                bash -c 'python3 {} -c {}' ".format(CONTAINER_NAME, os.path.join(MAIN_PATH, "intel/convert_intel.py"), config)
    cmd(command, SPLIT_ACTION)
    command = "docker stop {}".format(CONTAINER_NAME)
    cmd(command, SPLIT_ACTION)
