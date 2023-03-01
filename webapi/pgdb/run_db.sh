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
# Color ANIS
RED='\033[1;31m'
BLUE='\033[1;34m'
GREEN='\033[1;32m'
YELLOW='\033[1;33m'
CYAN='\033[1;36m'
NC='\033[0m';

# ---------------------------------------------------------
# Set the default value of the getopts variable 
PORT="6532"
COMMAND="bash"
WORKSPACE="/workspace"
CONF="./webapi/pgdb/pgdb.json"
DBNAME="postgres"
USER="postgres"
PASSWORD="admin"
CONTAINER_NAME="ivit_t_postgres"
DEFAULT_DBFOLDER="/var/lib/postgresql/data"
OUTSIDE_DBFOLDER="/webapi/pgdb"
DOCKER_IMAGE="postgres"
TAG_VER="latest"

# ---------------------------------------------------------
# help
function help(){
	echo "-----------------------------------------------------------------------"
	echo "Run the iVIT-T environment."
	echo
	echo "Syntax: scriptTemplate [-p|-s|mh]"
	echo "options:"
	echo "p		run container with Web API, setup the web api port number."
	echo "s		setup password in the database."
	echo "u		setup user in the database."
	echo "d		setup database name in the database."
    echo "m		Print information with magic"
	echo "h		help."
	echo "-----------------------------------------------------------------------"
}
while getopts "p:s:u:d:mh" option; do
	case $option in
		p )
			PORT=$OPTARG
			;;
		s )
			PASSWORD=$OPTARG
			;;
		u )
			USER=$OPTARG
			;;
		d )
			DBNAME=$OPTARG
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
# Writing in pgdb.json
sed -i  's/\("PORT":"\).*/\1'"$PORT"'",/g'   ./webapi/pgdb/pgdb.json
sed -i  's/\("DBNAME":"\).*/\1'"$DBNAME"'",/g'   ./webapi/pgdb/pgdb.json
sed -i  's/\("USER":"\).*/\1'"$USER"'",/g'   ./webapi/pgdb/pgdb.json
sed -i  's/\("PASSWORD":"\).*/\1'"$PASSWORD"'"/g'   ./webapi/pgdb/pgdb.json

# ---------------------------------------------------------
# Download samples
echo -e "${YELLOW}"
echo "-----Downloading samples-----"
echo -e "${NC}"

if [ -d "./project/fruit_object_detection" ]; then
	echo "-----The samples of directory does exists-----"
else
	FILEID="1mwmos6VD7p-VsVtDJcD-tzWizJm8NWWJ"
	STORREFILE="samples"
	wget --load-cookies /tmp/cookies.txt \
		"https://docs.google.com/uc?export=download&confirm=$(wget \
		--quiet --save-cookies /tmp/cookies.txt --keep-session-cookies \
		--no-check-certificate 'https://docs.google.com/uc?export=download&id='${FILEID}'' \
		-O- | sed -rn 's/.*confirm=([0-9A-Za-z_]+).*/1n/p')&id=${FILEID}" \
		-O "$STORREFILE" && rm -rf /tmp/cookies.txt
	unzip $STORREFILE
	rm $STORREFILE
	mv fruit_object_detection ./project
	mv dog_cat_classification ./project
fi

# ---------------------------------------------------------
# Open container
docker inspect ${CONTAINER_NAME} -f '{{.Name}}' > /dev/null
if [ $? -eq 0 ] ;then

	echo -e "${YELLOW}"
	echo "container:${CONTAINER_NAME} exist!"
	echo -e "${NC}"

	docker start ${CONTAINER_NAME}
else
# ---------------------------------------------------------
	# Run container
	DOCKER_CMD="docker run -dt \
	--name ${CONTAINER_NAME} \
	-p ${PORT}:5432 \
	-v `pwd`${OUTSIDE_DBFOLDER}:${DEFAULT_DBFOLDER} \
	-e PGDATA=/var/lib/postgresql/data/pgdata \
	-e POSTGRES_USER=${USER} \
	-e POSTGRES_PASSWORD=${PASSWORD} \
	-e POSTGRES_INITDB_ARGS='--data-checksums' \
	-e POSTGRES_DB=${DBNAME} \
	${DOCKER_IMAGE}:${TAG_VER}"

# ---------------------------------------------------------
	echo -e "${YELLOW}"
	echo "-----Command: ${DOCKER_CMD}-----"
	echo -e "${NC}"

	bash -c "${DOCKER_CMD}"

fi

