# iVIT-T

A library to training model of TensorFlow-Keras and Darknet. This library enables the training of the model of classification, object detection.
* [See What's New](#see-whats-new)
* [Pre-requirements](#pre-requirements)
* [Build convert docker images](#build-convert-docker-images)
* [CLI mode](#cli-mode)
* [Web API mode](#web-api-mode)
* [Web UI](#web-ui)

# See What's New
- [Release Notes](docs/release_notes.md)
- Training Classificaiton/Object detection model
- Simply evaluate model
- Convert model to edge platform
    - Intel(.xml/.bin/.mapping)
    - Nvidia(.onnx)
    - Xilinx(.xmodel)
- Offer Web API Can used to build project, uploading dataset, labeling, training, evaluating, converting

# Getting Started

### Pre-requirements
Install nvidia-driver(gpu), nvidia-docker and docker before installing the docker container.

- [Tutorial-nvidia-driver](https://docs.nvidia.com/datacenter/tesla/tesla-installation-notes/index.html)

- [Tutorial-docker](https://docs.docker.com/engine/install/ubuntu/)

- [Tutorial-nvidia-docker](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html#docker)

##  Run container

### Build convert docker images
```shell
sudo chmod 777 ./docker
sudo ./docker/build_convert.sh -p 0,1,2
```
In the "build_convert.sh", this "-p" is the model finally deployed platform:
```
0: Nvidia, 1: Intel, 2: Xilinx
```

### CLI mode

```shell
sudo ./docker/run.sh
```

- [Tutorial](./CLI.md)

### Web API mode

```shell
sudo ./docker/run.sh -p 6530
```

In the "run.sh", this "-p" is the port number, you can setting haven't used the port number.

- [Tutorial](./webapi/ReadME.md)

## Web UI
If you want to use the UI version, you can follow this Tutorial:

- [Tutorial](https://github.com/InnoIPA/ivit-t-web)