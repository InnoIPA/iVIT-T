#!/bin/bash
source ./docker/format_print.sh

# Initial
printd "$(date +"%T") Initialize ... " Cy
apt-get update -qqy
apt-get install -qy figlet boxes tree > /dev/null 2>&1
apt-get install -qy python3-pip
pip3 install --disable-pip-version-check --force pip~=21.0

ROOT=`pwd`
echo "Workspace is ${ROOT}" | boxes -p a1

# OpenCV
printd "$(date +"%T") Install OpenCV " Cy
apt-get install -qqy libsm6 libxext6 #> /dev/null 2>&1
apt-get install -y build-essential libopencv-dev
pip3 install -q --disable-pip-version-check opencv-python==4.5.3.56  #> /dev/null 2>&1
pip3 install -q --disable-pip-version-check opencv-contrib-python==4.5.3.56 #> /dev/null 2>&1

# Other packages
printd "$(date +"%T") Install other msicellaneous packages " Cy
pip3 install --disable-pip-version-check keras2onnx tf2onnx onnx onnxruntime keras_applications 
pip3 install --disable-pip-version-check pyyaml==5.4.1 colorlog
printd -e "Done${REST}"