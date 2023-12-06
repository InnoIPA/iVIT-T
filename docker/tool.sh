#!/bin/bash
# Copyright (c) 2023 Innodisk Corporation
# 
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

# Color ANIS
RED='\033[1;31m';
BLUE='\033[1;34m';
GREEN='\033[1;32m';
YELLOW='\033[1;33m';
CYAN='\033[1;36m';
NC='\033[0m';

#-------------------------------------------------------------
#Parameter setting
MODE=""
VERSION=""
FILE=$(realpath "$0")
ROOT=$(dirname "${FILE}")
P_PATH=$(dirname "${ROOT}")
CONF="${P_PATH}/docs/version.json"
TAG_VER=$(cat ${CONF} | jq -r '.VERSION')


#-------------------------------------------------------------
#import utils
source "${P_PATH}/docker/utils.sh"
#-------------------------------------------------------------
#Help function 
function help(){
	echo "-----------------------------------------------------------------------"
	echo "Run the iVIT-T update."
	echo
	echo "Syntax: scriptTemplate [-m|v]"
	echo "options:"
	echo "m		operator:"
	echo "			1.Recover."
	echo "			2.Update."
	echo "			3.Upgrade. (note: if you choise upgrade , make sure you enter version)"
	echo "v		version."
	echo "h		help."
	echo "-----------------------------------------------------------------------"
}


while getopts "m:v:h" option; do
	case $option in
		m )
			MODE=$OPTARG
			;;
		v )
			VERSION=$OPTARG
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

#------------------------------------------------------------
#Main function 

#Do recover
if [ "${MODE}" = 1 ];then
	echo -e "${YELLOW}"
	echo "Ready to recorver iVIT-T ${TAG_VER}!!"
	echo -e "${NC}"

	total_steps=3

	#clear all commit
	progress=$((1 * 100 / total_steps))
	draw_progress_bar $progress
	git restore .

	#discard change
	progress=$((2 * 100 / total_steps))
	draw_progress_bar $progress
	git reset

	#recorver
	progress=$((3 * 100 / total_steps))
	draw_progress_bar $progress
	git checkout .


fi

#Do update
if [ "${MODE}" = 2 ];then
	echo -e "${YELLOW}"
	echo "Ready to update iVIT-T ${TAG_VER} from official github!!"
	echo -e "${NC}"
	total_steps=4

	#clear all commit
	progress=$((1 * 100 / total_steps))
	draw_progress_bar $progress
	git restore .

	#discard change
	progress=$((2 * 100 / total_steps))
	draw_progress_bar $progress
	git reset

	#update all branch(this step can get new branch)
	progress=$((3 * 100 / total_steps))
	draw_progress_bar $progress
	git fetch

	#pull from github
	progress=$((4 * 100 / total_steps))
	draw_progress_bar $progress
	echo
	git pull

fi

#Do upgrade
if [ "${MODE}" = 3 ];then
	if [ "${VERSION}" = "" ];then
	
		echo -e "${RED}"
		echo "Your try to excute upgrade , but you didn't set version!"
		echo -e "${NC}"
		exit
	fi
	echo -e "${YELLOW}"
	echo "Ready to upgrade iVIT-T ${VERSION} from official github!!"
	echo -e "${NC}"
	total_steps=4

	#clear all commit
	progress=$((1 * 100 / total_steps))
	draw_progress_bar $progress
	git restore .

	#discard change
	progress=$((2 * 100 / total_steps))
	draw_progress_bar $progress
	git reset

	#update all branch(this step can get new branch)
	progress=$((3 * 100 / total_steps))
	draw_progress_bar $progress
	git fetch

	progress=$((4 * 100 / total_steps))
	draw_progress_bar $progress
	#change branch
	echo
	git checkout ${VERSION}

fi
