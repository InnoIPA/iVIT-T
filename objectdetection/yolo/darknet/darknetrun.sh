#!/bin/bash
if [ -z "$(find | grep libdarknet.so)" ]
then
    echo "The package of darknet is uninstalled."
    source ./docker/format_print.sh
    # Make Darknet
    printd "$(date +"%T") Darknet" Cy
    chmod -R 777 ./objectdetection/yolo/darknet
    cd ./objectdetection/yolo/darknet

    # select device
    chmod +x gpumakefile.sh && ./gpumakefile.sh 

    # buliding
    printd "$(date +"%T") make clean" Cy
    make clean
    printd "$(date +"%T") make" Cy
    make

    export Darknet="libdarknet.so is installed"
    source ~/.bashrc

    printd -e "Done${REST}"
else
    echo "The package of darknet is installed."
fi