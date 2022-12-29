#!/bin/bash
# ---------------------------------------------------------
# Set the default value of the getopts variable 
mount_gpu="--gpus=all"
workspace="/workspace"
main_container="ivit-t_test"
mode=false
docker_image="intel-convert"
docker_name=${docker_image}
# ---------------------------------------------------------
# help
function help(){
	echo "-----------------------------------------------------------------------"
	echo "Convert model."
	echo
	echo "Syntax: scriptTemplate [-p|m|h]"
	echo "options:"
	echo "m		Run code on terminal"	
	echo "h		help."
	echo "-----------------------------------------------------------------------"
}

while getopts "mh" option; do
	case $option in
		m )
			mode=true
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
# Open container mode
if [[ ${mode} == false ]]; then
	volume="--volumes-from ${main_container}"
else
	volume="-v `pwd`:${workspace}"
fi

# ---------------------------------------------------------
# open docker container
echo "-----Run container of intel-----"
intel_cmd="pip install colorlog && python3 ./convert/intel/convert_intel.py && clear"

# Run container
docker_cmd="docker run \
			--name ${docker_name} \
			${mount_gpu} \
			--user root \
			--rm -it \
			--net=host --ipc=host \
			-w ${workspace} \
			${volume}\
			-v /etc/localtime:/etc/localtime:ro \
			${docker_image} \"${intel_cmd}\""

echo ""
echo -e "Command: ${docker_cmd}"
echo ""
bash -c "${docker_cmd}"
echo "Converted."













