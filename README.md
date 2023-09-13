# iVIT-T

<div align="center">
  <img width="100%" height="100%" src="docs/thumbnail_iVIT-T Logo.png">
</div>

A library to training model of TensorFlow-Keras and Darknet. This library enables the training of the model of classification, object detection.
* [See What's New](#see-whats-new)
* [Pre-requirements](#pre-requirements)
* [Build convert docker images and database container](#build-convert-docker-images-and-database-container)
* [Web API mode](#web-api-mode)
* [Web UI](#web-ui)
* [The format of dataset](#the-format-of-dataset)
* [Reference](#reference)

# See What's New
- [Release Notes](docs/release_notes.md)
- Added new platform - Hailo
- Support convert to Hailo model
- Supoort export model to iCAP

# Getting Started

### Pre-requirements
Install **nvidia-driver(510+)**, **nvidia-docker** and **docker** before installing the docker container.

- [Tutorial-nvidia-driver](https://docs.nvidia.com/datacenter/tesla/tesla-installation-notes/index.html)

- [Tutorial-docker](https://docs.docker.com/engine/install/ubuntu/)

- [Tutorial-nvidia-docker](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html#docker)

- **Add docker to sudo group** 
    - [Tutourial](https://docs.docker.com/engine/install/linux-postinstall/)
    ``` 
    sudo groupadd docker
    sudo usermod -aG docker $USER
    sudo chmod 777 /var/run/docker.sock
    ```
    
##  Run container

### Build convert docker images and database container
```shell
sudo chmod 777 ./docker
sudo ./docker/init_env.sh -p 0,1,2,3
```
In the "init_env.sh", this "-p" is the model finally deployed platform:
```
0: Nvidia, 1: Intel, 2: Xilinx, 3: Hailo
```

### Web API mode

```shell
sudo ./docker/run.sh -p 6530
```

In the "run.sh", this "-p" is the port number, you can setting haven't used the port number.

- [Tutorial](./webapi/ReadME.md)

## Web UI
If you want to use the UI version, you can follow this Tutorial:

- [Tutorial](https://github.com/InnoIPA/ivit-t-web)

## The format of dataset 
- Image format: .jpg/.jpeg/.png/.bmp/.JPG/.JPEG/.PNG/.BMP

### Classification
- Folder(class)/img1, img2, ..., imgN
```
├── class_1
│   ├── 1.jpg
│   ├── 2.jpg
│   ├── 3.jpg
...
│   ├── 29.jpg
│   └── 30.jpg
└── class_2
    ├── 1.jpg
    ├── 2.jpg
    ├── 3.jpg
    ...
    ├── 29.jpg
    └── 30.jpg
```

### Object detection
- Folder/img1, txt1, img2, txt2, ..., imgN, txtN
```
Folder
├── 0.jpg
├── 0.txt
├── 10000.jpg
├── 10000.txt
├── 10001.jpg
├── 1000.jpg
├── 1000.txt
├── 10069.jpg
├── 10069.txt
├── 1006.jpg
├── 1006.txt
├── 10078.jpg
...
├── 840.jpg
└── 840.txt
```

- Annotation format: .txt (YOLO)
```
    Format:
        index x y w h
    Example:
        0 0.4014 0.3797 0.0801 0.0859
```
- Mapping class filename: classes.txt
```
    label1
    label2
    ...
```

# Reference
- Darknet
    - https://github.com/AlexeyAB/darknet
- Tensorflow
    - https://github.com/tensorflow/tensorflow
- OpenVINO:
    - https://docs.openvino.ai/latest/home.html
    - https://github.com/openvinotoolkit/openvino
- Vitis-AI:
    - https://github.com/Xilinx/Vitis-AI.git
    - https://github.com/Xilinx/Vitis-AI
- Hailo:
    - https://hailo.ai/developer-zone/documentation/sw-suite-2023-01-1/?sp_referrer=suite_install.html
    - https://github.com/hailo-ai/hailort
- To convert the model to someone format, we refer to the repository:
    - https://github.com/david8862/keras-YOLOv3-model-set
    - https://github.com/Tianxiaomo/pytorch-YOLOv4.git
- Flask
    - https://github.com/pallets/flask
- Sample images from Pexels
    - https://www.pexels.com/
- Sample images from roboflow
    - https://universe.roboflow.com/
- Segmentation models
    - https://github.com/qubvel/segmentation_models
    ```
    @misc{Yakubovskiy:2019,
        Author = {Pavel Iakubovskii},
        Title = {Segmentation Models},
        Year = {2019},
        Publisher = {GitHub},
        Journal = {GitHub repository},
        Howpublished = {\url{https://github.com/qubvel/segmentation_models}}
        }
    ```