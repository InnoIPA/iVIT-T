# CLI mode

## Prepare datasets 

[Tutorial](./Dataset.md)

## Download pre-trained model

[Tutorial](./pretrainedmodel/README.md)
<br>

## Training

### Setting config of training

Open to Project/samples/Config.json. Change the path of model_json to you will using the application.
<br>

```json
{
    "model_json":"Project/samples/classification.json",
    "platform": [
        "nvidia",
        "intel",
        "xilinx"
    ]
}
```

Create your folder of project, copy "Project/samples/model.json" to project folder, put dataset split train/val/test/eval folder in project folder, create weights folder in project folder.

If you want to change hyperparameters, you should be changed the content of Project/project folder/model.json.

### Example
```json
{
    "model_config": {
        "arch": "resnet",
        "classes":2,
        "input_shape": [675,177,3]
      },

    "train_config" :{
        "train_dataset_path": "/workspace/dataset/resnet/Memory_small/train",
        "val_dataset_path":"/workspace/dataset/resnet/Memory_small/valid",
        "test_dataset_path":"/workspace/dataset/resnet/Memory_small/test",
        "label_path":"/workspace/dataset/resnet/imagenet.names",
        "pretrained_model_path":"/workspace/pretrainedmodel/resnet_50.hdf5",
        "save_model_path":"/workspace/Classification/callback/model",
        "optimizer":{
            "sgd": {
            "lr": 0.01,
            "decay": 0.0,
            "momentum": 0.9,
            "nesterov": false
            }
        },

        "GPU":"0",
        "batch": 8,
        "epochs": 100,
        "workers": 16,
        .
        .
        .

    },
    .
    .
    .
}
```

### RUN
``` shell
python3 train.py
```

## Evaluate

### Setting config of Evaluation

Open to Config/evaluate.json. Change model_path, eval_dir_path.

```json
{
    "model_path": "./Project/test_cls/weights/model-best.h5",
    "eval_dir_path": "./Project/test_cls/dataset/eval"
}
```

### RUN
``` shell
python3 evaluate.py
```

## Covert

### Setting config of exprot

Open to Project/XXX/model.json. Change export_platform.

```json
{
    "platform":"xilinx",
    "export_platform":"xilinx",
}
```

### RUN
``` shell
python3 convert.py
```