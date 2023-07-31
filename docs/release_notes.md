# Release Notes
## Release 1.1.3
### Bug fix 
-When the project don't add any label , and then adding new label at upload , it will crash.

## Release 1.1.2
### Bug fix 
- After adding new label at upload, it will crash.

## Release 1.1.1
### New Features/Highlights
- Added save color id in the database for the class of dataset
- Unified format of response for web API

### Release Notes
### Web API
- Added save color id in the database for the class of dataset
- Unified format of response for web API

---
## Release 1.1
### New Features/Highlights
- Added new platform - Hailo
- Support convert to Hailo model
- Supoort export model to iCAP

### Release Notes
### Web API
- Added new platform - Hailo
- Support convert to Hailo model
- Supoort export model to iCAP

---
## Release 1.0.1
### New Features/Highlights
- Added database
### Release Notes
### Web API
- Added database

---
## Release 1.0
### New Features/Highlights
- Training Classificaiton/Object detection model
- Simply evaluate model
- Convert model to edge platform
    - Intel(.xml/.bin/.mapping)
    - Nvidia(.onnx)
    - Xilinx(.xmodel)
- Offer Web API Can used to build project, uploading dataset, labeling, training, evaluating, converting

### Release Notes
### Classification
- Training 
    - Intel: NGC-Resnet-18/ NGC-Resnet-50
    - Nvida: NGC-Resnet-18/ NGC-Resnet-50
    - Xilinx: Tensorflow-Vgg-16/ Tensorflow-Resnet-50
- Simply evaluate model
- Convert model to edge platform
    - Intel(.xml/.bin/.mapping)
    - Nvidia(.onnx)
    - Xilinx(.xmodel)

### Object Detection
- Training 
    - Intel: Darknet-YOLOv4/ Darknet-YOLOv4-tiny
    - Nvida: Darknet-YOLOv4/ Darknet-YOLOv4-tiny
    - Xilinx: Darknet-YOLOv4-leaky/ Darknet-YOLOv3-tiny
- Simply evaluate model
- Convert model to edge platform
    - Intel(.xml/.bin/.mapping)
    - Nvidia(.onnx)
    - Xilinx(.xmodel)

### Web API
- Building project
- Uploading dataset
- Labeling data
- Training model
- Evaluating model
- Converting model