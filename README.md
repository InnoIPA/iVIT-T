# iVIT-T

A library to training model of TensorFlow-Keras and Darknet. This library enables the training of the model of classification, object detection.
* [See What's New](#see-whats-new)
* [Pre-requirements](#pre-requirements)
* [Build docker images](#build-docker-images)
* [Build convert docker images and database container](#build-convert-docker-images-and-database-container)
* [CLI mode](#cli-mode)
* [Web API mode](#web-api-mode)
* [Web UI](#web-ui)

# See What's New
- [Release Notes](docs/release_notes.md)
- Added new platform - Hailo
- Support convert to Hailo model
- Supoort export model to iCAP

# Getting Started

### Pre-requirements
Install **nvidia-driver-525**(gpu, cuda-12.0.1), **nvidia-docker** and **docker** before installing the docker container.

- [Tutorial-nvidia-driver](https://docs.nvidia.com/datacenter/tesla/tesla-installation-notes/index.html)

- [Tutorial-docker](https://docs.docker.com/engine/install/ubuntu/)

- [Tutorial-nvidia-docker](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html#docker)

### Build docker images

```shell
sudo chmod 777 ./docker
sudo ./docker/build.sh -m
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

### CLI mode

```shell
sudo ./docker/run.sh
```

- [Tutorial](docs/CLI.md)

### Web API mode

```shell
sudo ./docker/run.sh -p 6530
```

In the "run.sh", this "-p" is the port number, you can setting haven't used the port number.

- [Tutorial](./webapi/ReadME.md)

## Web UI
If you want to use the UI version, you can follow this Tutorial:

- [Tutorial](https://github.com/Innodisk-Will/ivit-t-web-ui)

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