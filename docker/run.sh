#!/bin/bash
# --------------------------------------------------------
# Sub function
function print_magic(){
	info=$1
	magic=$2
	echo ""
	if [[ $magic = true ]];then
		echo -e $info | boxes -d dog -s 80x10
	else
		echo -e $info
	fi
	echo ""
}

# ---------------------------------------------------------
# color ANIS
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m';

# ---------------------------------------------------------
# Set the default value of the getopts variable 
GPU="all"
PORT=""
SERVER=false
MOUNT_GPU="--gpus"
SET_VERSION=""
COMMAND="bash"
WEB_API="./docker/run_web_api.sh"
WORKSPACE="/workspace"
CONF="./docs/version.json"
BACKRUN=false

# ---------------------------------------------------------
# help
function help(){
	echo "-----------------------------------------------------------------------"
	echo "Run the iVIT-T environment."
	echo
	echo "Syntax: scriptTemplate [-g|p|sh]"
	echo "options:"
	echo "g		select the target gpu."
	echo "p		run container with Web API, setup the web api port number."
	echo "s		Server mode for non vision user"
    echo "m		Print information with magic"
	echo "h		help."
	echo "-----------------------------------------------------------------------"
}
while getopts "g:p:sbmh" option; do
	case $option in
		g )
			GPU=$OPTARG
			;;
		p )
			PORT=$OPTARG
			;;
		s )
			SERVER=true
			;;
		b )
			BACKRUN=true
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

# ---------------------------------------------------------
# Install jq
echo -e "${YELLOW}"
echo "-----Installing jq-----"
echo -e "${NC}"

sudo apt-get install -y jq

# ---------------------------------------------------------
# Get version number
echo -e "${YELLOW}"
echo "-----Get version number-----"
echo -e "${NC}"

TAG_VER=$(cat ${CONF} | jq -r '.VERSION')
USER=$(cat ${CONF} | jq -r '.USER')
BASE_NAME=$(cat ${CONF} | jq -r '.PROJECT')

DOCKER_IMAGE="${USER}/${BASE_NAME}"
CONTAINER_NAME="${BASE_NAME}"

# ---------------------------------------------------------
# SERVER or DESKTOP MODE
if [ ${SERVER} ];then
	MODE="DESKTOP"
	SET_VERSION="-v /tmp/.x11-unix:/tmp/.x11-unix:rw -e DISPLAY=unix${DISPLAY}"
	# let display could connect by every device
	xhost + > /dev/null 2>&1
else
	MODE="SERVER"
fi

# ---------------------------------------------------------
# Combine gpu option
MOUNT_GPU="${MOUNT_GPU} device=${GPU}"

# ---------------------------------------------------------
# If port is available, run the WEB API
if [[ -n ${PORT} ]];then 
	# COMMAND="python3 ${WEB_API} --host 0.0.0.0 --port ${port} --af ${framework}"
	COMMAND="source ${WEB_API} -p ${PORT}"
fi

# ---------------------------------------------------------
TITLE="\n\
PROGRAMMER: Welcome to iVIT-T \n\
MODE:  ${MODE}\n\
DOCKER: ${DOCKER_IMAGE} \n\
VERSION: ${TAG_VER} \n\
PORT: ${PORT} \n\
GPU:  ${GPU}\n\
COMMAND: ${COMMAND}"

print_magic "${TITLE}" "${MAGIC}"

# ---------------------------------------------------------
# Bulid darknet & check status
if [ "${BACKRUN}" = true ];then
	DARKNET=""
	RUNCODE="-dt"
	BASHCODE="bash"
else
	DARKNET="chmod +x ./ObjectDetection/YOLO/darknet/darknetrun.sh && ./ObjectDetection/YOLO/darknet/darknetrun.sh"
	DLPRETRAINED="python3 pretrainedmodel/pretrained_download.py -all"
	RUNCODE="-it"
	BASHCODE="bash -c \"${DARKNET} && ${DLPRETRAINED} && ${COMMAND} \" "
fi

# ---------------------------------------------------------
# Run container
DOCKER_CMD="docker run \
--name ${CONTAINER_NAME}_run \
${MOUNT_GPU} \
--user root \
--rm ${RUNCODE} \
-v /dev:/dev \
--net=host --ipc=host \
-w ${WORKSPACE} \
-v `pwd`:${WORKSPACE} \
-v /etc/localtime:/etc/localtime:ro \
-v /var/run/docker.sock:/var/run/docker.sock \
${SET_VERSION} \
${DOCKER_IMAGE}:${TAG_VER} \
${BASHCODE}"

# ---------------------------------------------------------
echo -e "${YELLOW}"
echo "-----Command: ${DOCKER_CMD}-----"
echo -e "${NC}"

bash -c "${DOCKER_CMD}"
