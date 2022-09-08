import sys, os
import subprocess, shutil
import logging
# Append to API
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[2]/"common"))
from logger import config_logger
from utils import read_json 

def cmd(command):
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,shell=True)
    for line in iter(process.stdout.readline,b''):
        line = line.rstrip().decode('ascii',errors='ignore')

        if line.isspace(): 
            continue
        else:
            print(line)

def main():
    command = "./convert/xilinx/Vitis-AI/vitis-ai-start.sh c"
    cmd(command)
    command = "docker exec -it vitis-ai-ivit-t bash -c  'source /opt/vitis_ai/conda/bin/activate vitis-ai-tensorflow && pip install colorlog && python3 ./convert/xilinx/convert_xilinx.py' "
    cmd(command)
    command = "clear"
    cmd(command)
    command = "docker stop vitis-ai-ivit-t && docker rm vitis-ai-ivit-t"
    cmd(command)

if __name__ == '__main__':
    config_logger('./convert.log', 'a', "info")
    sys.exit(main() or 0)
