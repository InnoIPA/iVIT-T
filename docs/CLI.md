# CLI mode

## Prepare datasets 

- [Tutorial](./Dataset.md)

## Download pre-trained model

- [Tutorial](./pretrainedmodel/README.md)
<br>

## Training

### Setting config of training

Create your folder of project, copy **"/project/samples/model.json"** to project folder, put dataset split **"train/val/test/eval"** folder in project folder, create weights folder in project folder.

If you want to change hyperparameters, you should be changed the content of **"./project/project_folder/model.json"**.

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

        "gpu":"0",
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
python3 train.py -c model.json
```
The -c is the path of model.json.</br>
> Example: `./project/dog_cat_classification/iteration1/classfication.json`

## Get metrics

### RUN

```shell
python3 get_metrics.py -c model.json
```

The -c is path of training model.json.

> Example: `./project/dog_cat_classification/iteration1/classfication.json`

## Evaluate

### Setting config of Evaluation

Open to **"./project/project_folder/model.json"**. Change value of **eval_dir_path** in **eval_config**.

```json
{
    "eval_config":{
        "eval_dir_path":"./project/yolov3-tiny-vitisai/iteration1/dataset/eval"
    }
}
```

### RUN
``` shell
python3 evaluate.py -c model.json
```
The -c is the path of model.json.</br>
> Example: `./project/dog_cat_classification/iteration1/classfication.json`

## Covert

### Setting config of exprot

Open to **"./project/project_folder/model.json"**. Change value of **export_platform**.

```json
{
    "platform":"xilinx",
    "export_platform":"xilinx",
}
```

### RUN
``` shell
python3 convert.py -c model.json
```
The -c is the path of model.json.</br>
> Example: `./project/dog_cat_classification/iteration1/classfication.json`