import sys, subprocess, argparse
# Append to API
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[2]/"common"))
from logger import config_logger

def cmd(command):
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,shell=True)
    for line in iter(process.stdout.readline,b''):
        line = line.rstrip().decode('ascii',errors='ignore')

        if line.isspace(): 
            continue
        else:
            print(line)

def main(args):
    command = "./convert/intel/run.sh"
    cmd(command)
    command = "docker exec -it intel-convert \
                bash -c 'pip install colorlog && \
                python3 ./convert/intel/convert_intel.py -c {}' ".format(args.config)
    cmd(command)
    command = "docker stop intel-convert"
    cmd(command)

if __name__ == '__main__':
    config_logger('./convert.log', 'a', "info")
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', help = "The path of model config")
    args = parser.parse_args()
    sys.exit(main(args) or 0)