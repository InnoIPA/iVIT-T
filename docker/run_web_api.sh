#!/bin/bash

function Help()
{
   # Display Help
   echo "Run the docker container."
   echo
   echo "Syntax: scriptTemplate [-p|h]"
   echo "options:"
   echo "p		port number. e.g. 5000"
   echo "h		help."
   echo
}

while getopts "p:h" option; do
	case $option in
		p )
			PORT=$OPTARG
			;;
		h )
			Help
			exit;;
		\? )
			exit;;
	esac
done

# main
python3 app.py -port ${PORT}