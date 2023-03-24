#!/bin/bash
# ---------------------------------------------------------
# Color ANIS
RED='\033[1;31m'
BLUE='\033[1;34m'
GREEN='\033[1;32m'
YELLOW='\033[1;33m'
CYAN='\033[1;36m'
NC='\033[0m';

# Initial
echo -e "${BLUE}"
echo "$(date +"%T") Initialize ... "
echo -e "${NC}"

apt-get update -qqy
apt-get install -qy figlet boxes tree > /dev/null 2>&1
apt-get install -qy python3-pip
pip3 install --disable-pip-version-check --force pip~=21.0

ROOT=`pwd`
echo "Workspace is ${ROOT}" | boxes -p a1

# OpenCV
echo -e "${BLUE}"
echo "$(date +"%T") Install OpenCV "
echo -e "${NC}"
apt-get install -qqy libsm6 libxext6 #> /dev/null 2>&1
apt-get install -y build-essential libopencv-dev
pip3 install -q --disable-pip-version-check opencv-python==4.5.3.56  #> /dev/null 2>&1
pip3 install -q --disable-pip-version-check opencv-contrib-python==4.5.3.56 #> /dev/null 2>&1

# Other packages
echo -e "${BLUE}"
echo "$(date +"%T") Install other msicellaneous packages "
echo -e "${NC}"
pip3 install --disable-pip-version-check keras2onnx tf2onnx onnx onnxruntime keras_applications 
pip3 install --disable-pip-version-check pyyaml==5.4.1 colorlog matplotlib

echo -e "${BLUE}"
echo "Done${REST}"
echo -e "${NC}"