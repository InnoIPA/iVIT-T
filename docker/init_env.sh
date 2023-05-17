#!/bin/bash
# Copyright (c) 2023 Innodisk Corporation
# 
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

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

function google_download(){
    wget --load-cookies /tmp/cookies.txt \
    "https://docs.google.com/uc?export=download&confirm=$(wget \
    --quiet --save-cookies /tmp/cookies.txt --keep-session-cookies \
    --no-check-certificate 'https://docs.google.com/uc?export=download&id='$1'' \
    -O- | sed -rn 's/.*confirm=([0-9A-Za-z_]+).*/1n/p')&id=$1" \
    -O "$2" && rm -rf /tmp/cookies.txt
}

# ---------------------------------------------------------
# Set the default value of the getopts variable 
platform="0,1,2,3"
platform_list=('nvidia' 'intel' 'xilinx' 'hailo')

# ---------------------------------------------------------
# Color ANIS
RED='\033[1;31m';
BLUE='\033[1;34m';
GREEN='\033[1;32m';
YELLOW='\033[1;33m';
CYAN='\033[1;36m';
NC='\033[0m';

# ---------------------------------------------------------
# help
function help(){
    echo "-----------------------------------------------------------------------"
    echo "Build the iVIT-T environment."
    echo
    echo "Syntax: scriptTemplate [-p|m|h]"
    echo "options:"
    echo "p		Select any platform.(item: [0:nvidia, 1:intel, 2:xilinx, 3:hailo]) ex: -p '1,2' "
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
echo "----- Installing jq to write JSON -----"
apt-get install -y jq
echo "----- Installing wget to download file -----"
apt-get install -y wget
echo "----- Installing unzip file -----"
apt-get install -y unzip

# ---------------------------------------------------------
# Check input platform in platform_list
arr_index=(${platform//,/ })
out_platform=""
mv project/samples/platform.json project/samples/temp.json
for i in ${arr_index[@]}
do
    # echo "$i"
    # echo ${platform_list[i]} 
    out_platform+="\"${platform_list[i]}\","
    # out_platform+=","
    # echo ${out_platform}
done

# Writing json platform
jq -r '.platform |= ['${out_platform:0:-1}']' ./project/samples/temp.json > ./project/samples/platform.json
rm ./project/samples/temp.json

# ---------------------------------------------------------
title="\n\
PROGRAMMER: Welcome to iVIT-T \n\
Platform: ${out_platform:0:-1}"

print_magic "${title}" "${magic}"

# --------------------------------------------------------
# Builing Database
echo -e "${YELLOW}"
echo " +-+-+-+-+-+-+-+ +-+-+-+-+-+-+-+-+"
echo " |B|u|i|l|i|n|g| |D|a|t|a|b|a|s|e|"
echo " +-+-+-+-+-+-+-+ +-+-+-+-+-+-+-+-+"
echo -e "${NC}"

# sudo rm -r ./webapi/pgdb/pgdata
sudo ./webapi/pgdb/run_db.sh -p 6535 -s ivit_admin -d ivit -u ivit

# --------------------------------------------------------
# Pull convert images
echo -e "${YELLOW}"
echo " +-+-+-+-+ +-+-+-+-+-+-+-+ +-+-+-+-+-+-+"
echo " |P|u|l|l| |c|o|n|v|e|r|t| |i|m|a|g|e|s|"
echo " +-+-+-+-+ +-+-+-+-+-+-+-+ +-+-+-+-+-+-+"
echo -e "${NC}"

for i in ${arr_index[@]}
do
    if [[ ${i} == *"0"* ]]; then
        echo -e "${GREEN}"
        echo "----- Building image of nvidia -----"
        echo -e "${NC}"
    fi
    if [[ ${i} == *"1"* ]]; then
        echo -e "${BLUE}"
        echo "----- Building image of intel -----"
        echo -e "${NC}"
        docker build -t intel-convert -f ./convert/intel/intel.Dockerfile ./convert --no-cache
    fi
    if [[ ${i} == *"2"* ]]; then
        echo -e "${RED}"
        echo "----- Building image of xilinx -----"
        echo -e "${NC}"
        
        cd ./convert/xilinx
        git clone --recurse-submodules --branch 2.5 https://github.com/Xilinx/Vitis-AI 
        docker pull xilinx/vitis-ai-cpu:2.5.0
        # download convert folder
        cd ./Vitis-AI
        echo "----- Download conver folder of xilinx -----"
        FILEID="1yzYhz6T2u2GNCoqVjRcwaHDJ1_QoTBQk"
        STORREFILE="vitis-ai-utility.zip"
        google_download $FILEID $STORREFILE
        unzip $STORREFILE
        rm $STORREFILE
        cp ./vitis-ai-utility/vitis-ai-start.sh ./vitis-ai-start.sh
        cp ./vitis-ai-utility/docker_run.sh ./docker_run.sh
        cd ..
        cd ..
    fi
    if [[ ${i} == *"3"* ]]; then
        echo -e "${CYAN}"
        echo "----- Building image of hailo -----"
        echo -e "${NC}"

        cd ./hailo
        FILEID="1IFoof3TjeN2o7yBSZDhYR_GsMy_mC53V"
        STORREFILE="hailo_sw_suite_2023-01.zip"
        google_download $FILEID $STORREFILE
        unzip $STORREFILE
        rm $STORREFILE
        # Download hailo docker/convert package
        echo "----- Download conver folder of hailo -----"
        FILEID="1UvoBn8eEP91goi9-wg3bS90vFRuaUgIv"
        STORREFILE="pytorch-YOLO.zip"
        google_download $FILEID $STORREFILE
        unzip $STORREFILE
        rm $STORREFILE
    fi
done

echo "----- Finish -----"
