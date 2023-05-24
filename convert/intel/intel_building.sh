#!/bin/bash
# Copyright (c) 2023 Innodisk Corporation
# 
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

# --------------------------------------------------------
CONF="./docs/version.json"
ROOT=$(dirname "${FILE}")

# ---------------------------------------------------------
# Color ANIS
RED='\033[1;31m';
BLUE='\033[1;34m';
GREEN='\033[1;32m';
YELLOW='\033[1;33m';
CYAN='\033[1;36m';
NC='\033[0m';

# ---------------------------------------------------------
function ivit_word(){
  echo -e "${YELLOW}"
  echo '   
   _____     _ _   _ _         
  | __  |_ _| |_|_| |_|___ ___ 
  | __ -| | | | | . | |   | . |
  |_____|___|_|_|___|_|_|_|_  |
                          |___|

  '
  echo -e "${NC}"
}

ivit_word

# ---------------------------------------------------------
# Install jq
echo -e "${YELLOW}"
echo "----- Installing jq -----"
echo -e "${NC}"

if ! type jq >/dev/null 2>&1; then
    sudo apt-get install -y jq
else
    echo 'The jq has been installed.';
fi

# --------------------------------------------------------
# Parse information from configuration
CONF="./docs/version.json"
USER=$(cat ${CONF} | jq -r '.USER')
BASE_NAME="intel-convert"
TAG_VER="latest"

# --------------------------------------------------------
# Concate name
IMAGE_NAME="${USER}/${BASE_NAME}:${TAG_VER}"
echo -e "${YELLOW}"
echo "----- Concatenate docker image name: ${IMAGE_NAME} -----"
echo -e "${NC}"

# --------------------------------------------------------
# Build docker image
echo -e "${YELLOW}"
echo " +-+-+-+-+-+ +-+-+-+-+-+-+ +-+-+-+-+-+"
echo " |B|u|i|l|d| |d|o|c|k|e|r| |i|m|a|g|e|"
echo " +-+-+-+-+-+ +-+-+-+-+-+-+ +-+-+-+-+-+"
echo -e "${NC}"

docker build -t "${IMAGE_NAME}" -f ./convert/intel/intel.Dockerfile ./convert --no-cache

# ---------------------------------------------------------
# Push dockerhub
IMAGE_NAME="${USER}/${BASE_NAME}:${TAG_VER}"
echo -e "${GREEN}"
echo "----- Push dockerhub ${IMAGE_NAME} -----"
echo -e "${NC}"
docker push ${IMAGE_NAME}