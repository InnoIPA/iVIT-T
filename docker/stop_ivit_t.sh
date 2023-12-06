#!/bin/bash
# Copyright (c) 2023 Innodisk Corporation
# 
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT
FILE=$(realpath "$0")
ROOT=$(dirname "${FILE}")
source "${ROOT}/utils.sh"

total_steps=3
# --------------------------------------------------------
# Color
RED='\033[1;31m';
BLUE='\033[1;34m';
GREEN='\033[1;32m';
YELLOW='\033[1;33m';
CYAN='\033[1;36m';
NC='\033[0m';

echo -e "${YELLOW}"
echo "----- Close iVIT-T -----"
echo -e "${NC}"

progress=$((1 * 100 / total_steps))
draw_progress_bar $progress 

docker stop ivit-t > /dev/null 2>&1 || echo " ,Stop iVIT-T service failed."

progress=$((2 * 100 / total_steps))
draw_progress_bar $progress 
docker stop ivit-t-website > /dev/null 2>&1 || echo " ,Stop iVIT-T website failed."

progress=$((3 * 100 / total_steps))
draw_progress_bar $progress 
docker stop ivit-t-postgres > /dev/null 2>&1 || echo " ,Stop iVIT-T database failed." 

echo -e "${YELLOW}"
echo "Finished Close iVIT-T."
echo -e "${NC}"
