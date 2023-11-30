#!/bin/bash

# Variable
PORT=${1}

# Parameters
SERVICE="ivit-t"
SERV_FILE=""
SERV="ivit-t.service"
EXEC_CMD=""
OPTS="-p"
# Double Check
if [[ -z ${PORT} || ${PORT} = "-h" || ${PORT} = "--help" ]]; then
	echo "Please setup platform ..."
	echo ""
	echo "Usage:  install.sh [PORT]."
	echo ""
	echo "	- PORT: What port that you want to use? default is 6530."
	exit
fi

# Helper
function update_service_file() {
	root=$2
	file=$1
	start_cmd="$(realpath ${root})/docker/run.sh ${OPTS} ${PORT} -i"
	stop_cmd="$(realpath ${root})/docker/stop_ivit_t.sh"

	sed -i 's#ExecStart=.*#ExecStart='"${start_cmd}"'#g' $file
	sed -i 's#ExecStop=.*#ExecStop='"${stop_cmd}"'#g' $file
}


# Store the utilities
FILE=$(realpath "$0")
DOCKER_ROOT=$(dirname "${FILE}")
ROOT=$(dirname "${DOCKER_ROOT}")

# Disclaimer
${DOCKER_ROOT}/disclaimer.sh

if [ $? -eq 1 ];then 
    echo "Quit."; exit 0; 
fi

SERV_FILE="$(realpath ${DOCKER_ROOT})/service/${SERV}"

echo "Using service file: ${SERV_FILE}"

# Modify .service file
update_service_file ${SERV_FILE} "${ROOT}" 

# Change Permission
sudo chmod 644 ${SERV_FILE}

# Move to /etc/systemd/system
cp ${SERV_FILE} /etc/systemd/system/${SERVICE}.service

# Reload Service
sudo systemctl daemon-reload

# Start Service
sudo systemctl start ${SERVICE}
# systemctl status ${SERVICE}

# Enable Service when startup
sudo systemctl enable ${SERVICE}