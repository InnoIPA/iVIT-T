#!/bin/bash
# Copyright (c) 2023 Innodisk Corporation
# 
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

# ---------------------------------------------------------
# Color ANIS
RED='\033[1;31m';
BLUE='\033[1;34m';
GREEN='\033[1;32m';
YELLOW='\033[1;33m';
CYAN='\033[1;36m';
NC='\033[0m';

# ---------------------------------------------------------
# Install JQ
echo -e "${YELLOW}"
echo "----- Installing JQ -----"
echo -e "${NC}"

if ! type jq >/dev/null 2>&1; then
    sudo apt-get install -y jq
else
    echo 'The jq has been installed.';
fi

# ---------------------------------------------------------
# Get version number
MAIN="./webui/"
CONF="${MAIN}web_version.json"
TAG_VER=$(cat ${CONF} | jq -r '.VERSION')
DOCKER_USER=$(cat ${CONF} | jq -r '.USER')
BASE_NAME=$(cat ${CONF} | jq -r '.PROJECT')

# DOCKER_IMAGE="${USER}/${BASE_NAME}"
DOCKER_IMAGE="${BASE_NAME}"
CONTAINER_NAME="${BASE_NAME}"
IMAGE_NAME="${DOCKER_USER}/${BASE_NAME}:${TAG_VER}"

echo -e "${YELLOW}"
echo "----- .tar name:${DOCKER_IMAGE}.${TAG_VER}.tar -----"
echo -e "${NC}"

docker load < ${MAIN}${DOCKER_IMAGE}'.'${TAG_VER}'.tar'

echo -e "${GREEN}"
echo "----- Tag ${IMAGE_NAME} -----"
echo -e "${NC}"
docker tag ${DOCKER_IMAGE}:${TAG_VER} ${IMAGE_NAME}

echo -e "${GREEN}"
echo "----- Push dockerhub ${IMAGE_NAME} -----"
echo -e "${NC}"
# docker login --username=${DOCKER_USER} --password-stdin=${DOCKER_PASS}
docker push ${IMAGE_NAME}