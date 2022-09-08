DEV=`nvidia-smi -L`
echo ${DEV}

if [[ $DEV == *"GeForce"* ]];then
    if [[ $DEV == *"3070"* ]] || [[ $DEV == *"3080"* ]]  || [[ $DEV == *"3090"* ]];then
        sed -ie 's/# ARCH= -gencode arch=compute_86,code=[sm_86,compute_86]/ARCH= -gencode arch=compute_86,code=[sm_86,compute_86]/g' Makefile

    elif [[ $DEV == *"2080"* ]] || [[ $DEV == *"2070"* ]];then
        sed -ie 's/# ARCH= -gencode arch=compute_75,code=[sm_75,compute_75]/ARCH= -gencode arch=compute_75,code=[sm_75,compute_75]/g' Makefile
    fi

elif [[ $DEV == *"Tesla"* ]];then
    if [[ $DEV == *"A100"* ]] || [[ $DEV == *"GA100"* ]] || [[ $DEV == *"DGX-A100"* ]] || [[ $DEV == *"RTX 3080"* ]];then
        sed -ie 's/# ARCH= -gencode arch=compute_80,code=[sm_80,compute_80]/ARCH= -gencode arch=compute_80,code=[sm_80,compute_80]/g' Makefile
    elif [[ $DEV == *"V100"* ]];then
        sed -ie 's/# ARCH= -gencode arch=compute_70,code=[sm_70,compute_70]/ARCH= -gencode arch=compute_70,code=[sm_70,compute_70]/g' Makefile
    elif [[ $DEV == *"P4"* ]];then
        sed -ie 's/# ARCH= -gencode arch=compute_61,code=sm_61 -gencode arch=compute_61,code=compute_61/ARCH= -gencode arch=compute_61,code=sm_61 -gencode arch=compute_61,code=compute_61/g' Makefile
    elif [[ $DEV == *"P100"* ]];then
        sed -ie 's/# ARCH= -gencode arch=compute_60,code=sm_60/ARCH= -gencode arch=compute_60,code=sm_60/g' Makefile
    elif [[ $DEV == *"GA10x"* ]] || [[ $DEV == *"3090"* ]] || [[ $DEV == *"3080"* ]] || [[ $DEV == *"3070"* ]] || [[ $DEV == *"A6000"* ]] || [[ $DEV == *"A40"* ]];then
        sed -ie 's/# ARCH= -gencode arch=compute_86,code=[sm_86,compute_86]/ARCH= -gencode arch=compute_86,code=[sm_86,compute_86]/g' Makefile
    fi

elif [[ $DEV == *"1080"* ]] || [[ $DEV == *"1070"* ]] || [[ $DEV == *"1060"* ]] || [[ $DEV == *"1050"* ]] || [[ $DEV == *"1030"* ]];then
    sed -ie 's/# ARCH= -gencode arch=compute_61,code=sm_61 -gencode arch=compute_61,code=compute_61/ARCH= -gencode arch=compute_61,code=sm_61 -gencode arch=compute_61,code=compute_61/g' Makefile

fi