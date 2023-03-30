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
# function ivit_word(){
#   echo -e "${RED}"
#   echo "
#   ====================================================
#     _  ____   ____  _____  _________        _________  
#    (_)|_  _| |_  _||_   _||  _   _  |      |  _   _  | 
#    __   \ \   / /    | |  |_/ | | \_|______|_/ | | \_| 
#   [  |   \ \ / /     | |      | |   |______|   | |     
#    | |    \ ' /     _| |_    _| |_            _| |_    
#   [___]    \_/     |_____|  |_____|          |_____|   
	
#   ====================================================
#   "
#   echo -e "${NC}"
# }
# ivit_word

# ---------------------------------------------------------
# Set the default value of the getopts variable 
PORT=""
COMMAND="bash"
WORKSPACE="/etc/nginx/html"
CONF="./webui/web_version.json"

# ---------------------------------------------------------
# help
function help(){
	echo "-----------------------------------------------------------------------"
	echo "Run the iVIT-T Web Service."
	echo
	echo "Syntax: scriptTemplate [-p|h]"
	echo "options:"
	echo "p		run container with Web API, setup the web api port number."
    echo "m		Print information with magic"
	echo "h		help."
	echo "-----------------------------------------------------------------------"
}
while getopts "p:mh" option; do
	case $option in
		p )
			PORT=$OPTARG
			;;
        m )
			MAGIC=true
			;;
		h )
			help
			exit
			;;
		\? )
			help
			exit
			;;
		* )
			help
			exit
			;;
	esac
done

# # ---------------------------------------------------------
# # Install JQ
# echo -e "${GREEN}"
# echo "----- Installing JQ -----"
# echo -e "${NC}"

# if ! type jq >/dev/null 2>&1; then
#     sudo apt-get install -y jq
# else
#     echo 'The jq has been installed.';
# fi

# ---------------------------------------------------------
# Get version number
TAG_VER=$(cat ${CONF} | jq -r '.VERSION')
USER=$(cat ${CONF} | jq -r '.USER')
BASE_NAME=$(cat ${CONF} | jq -r '.PROJECT')
WEB_PORT=$(cat ${CONF} | jq -r '.WEB_PORT')

DOCKER_IMAGE="${USER}/${BASE_NAME}"
CONTAINER_NAME="${BASE_NAME}"

mv ${CONF} ./temp.json
# Writing json platform
jq -r '.API_PORT |= '${PORT}'' ./temp.json > ${CONF}
rm ./temp.json

echo -e "${GREEN}"
echo "----- UI version number:${TAG_VER} -----"
echo -e "${NC}"

# ---------------------------------------------------------
# Run container
DOCKER_CMD="docker run \
            --name ${CONTAINER_NAME} \
            --rm -dt \
            --net=host --ipc=host \
            -e API_PORT=${PORT} \
			-e WEB_PORT=${WEB_PORT} \
            -w ${WORKSPACE} \
            -v /etc/localtime:/etc/localtime:ro \
            ${DOCKER_IMAGE}:${TAG_VER}"

# ---------------------------------------------------------
echo -e "${GREEN}"
echo "----- Command: ${DOCKER_CMD} -----"
echo -e "${NC}"

bash -c "${DOCKER_CMD}"
