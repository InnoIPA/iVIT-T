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
# Set the default value of the getopts variable 
platform="0,1,2"
platform_list=('nvidia' 'intel' 'xilinx')

# ---------------------------------------------------------
# color ANIS
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m';

# ---------------------------------------------------------
# help
function help(){
	echo "-----------------------------------------------------------------------"
	echo "Build the iVIT-T environment."
	echo
	echo "Syntax: scriptTemplate [-p|m|h]"
	echo "options:"
	echo "p		Select any platform.(item: [0:nvidia, 1:intel, 2:xilinx]) ex: -p '1,2' "
    echo "m		Print information with magic"
	echo "h		help."
	echo "-----------------------------------------------------------------------"
}

while getopts "p:mh" option; do
	case $option in
		p )
			platform=$OPTARG
			;;
        m )
			magic=true
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
# apt install jq, wget, unzip
echo "-----Installing jq to write JSON-----"
apt-get install -y jq
echo "-----Installing wget to download file-----"
apt-get install -y wget
echo "-----Installing unzip file-----"
apt-get install -y unzip

# ---------------------------------------------------------
# Check input platform in platform_list
arr_index=(${platform//,/ })
out_platform=""
mv Project/samples/Config.json Project/samples/temp.json
for i in ${arr_index[@]}
do
    # echo "$i"
    # echo ${platform_list[i]} 
    out_platform+="\"${platform_list[i]}\","
    # out_platform+=","
    # echo ${out_platform}
done

# Writing json platform
jq -r '.platform |= ['${out_platform:0:-1}']' ./Project/samples/temp.json > ./Project/samples/Config.json
rm ./Project/samples/temp.json

# ---------------------------------------------------------
title="\n\
PROGRAMMER: Welcome to iVIT-T \n\
Platform: ${out_platform:0:-1}"

print_magic "${title}" "${magic}"

# --------------------------------------------------------
# Pull convert images
echo -e "${RED}"
echo " +-+-+-+-+ +-+-+-+-+-+-+-+ +-+-+-+-+-+-+"
echo " |P|u|l|l| |c|o|n|v|e|r|t| |i|m|a|g|e|s|"
echo " +-+-+-+-+ +-+-+-+-+-+-+-+ +-+-+-+-+-+-+"
echo -e "${NC}"

for i in ${arr_index[@]}
do
    if [[ ${i} == *"0"* ]]; then
		echo -e "${GREEN}"
        echo "-----Build image of nvidia-----"
		echo -e "${NC}"
    fi
    if [[ ${i} == *"1"* ]]; then
		echo -e "${BLUE}"
        echo "-----Build image of intel-----"
		echo -e "${NC}"
		docker build -t intel-convert -f ./convert/intel/intel.Dockerfile ./convert --no-cache
    fi
    if [[ ${i} == *"2"* ]]; then
		echo -e "${RED}"
        echo "-----Build image of xilinx-----"
		echo -e "${NC}"
		
        cd ./convert/xilinx
        git clone --recurse-submodules --branch 1.4 https://github.com/Xilinx/Vitis-AI 
		docker pull xilinx/vitis-ai-cpu:1.4.1.978
		# download convert folder
		cd ./Vitis-AI
		echo "-----Download conver folder of xilinx-----"
		FILEID="1yzYhz6T2u2GNCoqVjRcwaHDJ1_QoTBQk"
		STORREFILE="vitis-ai-utility.zip"
		wget --load-cookies /tmp/cookies.txt \
			"https://docs.google.com/uc?export=download&confirm=$(wget \
			--quiet --save-cookies /tmp/cookies.txt --keep-session-cookies \
			--no-check-certificate 'https://docs.google.com/uc?export=download&id='${FILEID}'' \
			-O- | sed -rn 's/.*confirm=([0-9A-Za-z_]+).*/1n/p')&id=${FILEID}" \
			-O "$STORREFILE" && rm -rf /tmp/cookies.txt
		unzip $STORREFILE
		rm $STORREFILE
		cp ./vitis-ai-utility/vitis-ai-start.sh ./vitis-ai-start.sh
		cp ./vitis-ai-utility/docker_run.sh ./docker_run.sh
    fi
done

echo "-----Finish-----"
