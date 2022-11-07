import os
import sys
import json
import logging
import traceback
import numpy as np
import random
import tensorflow as tf
from tensorflow import keras

# Append to API
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]/"common"))
from logger import config_logger
from utils import read_json, write_json
from setting import Setting
from augmentation import Augmentation
from callback import Callback
from model import BulidingModel
from metrics import test_summary, metrics_report
random.seed(5)

def get_model_summary(model: tf.keras.Model) -> str:
    string_list = []
    model.summary(line_length=80, print_fn=lambda x: string_list.append(x))
    return "\n".join(string_list)

def main():
    # Instantiation
    Init_set = Setting()

    # Get model relative info
    logging.info("Loading config!")
    Dict = read_json(read_json("./Project/samples/Config.json")['model_json'])
    Init_set.checkpath(Dict)
    
    # Setting device
    logging.info("Setting GPU!")
    Init_set.setting_device(Dict['train_config']['GPU'])

    # DataProcessing
    logging.info("Augmentation!")
    Dataset = Augmentation(Dict)

    # Channel change
    keras.backend.set_image_data_format(Dataset.data_format)

    # Loading Pretrained model and initail model
    keras.backend.set_learning_phase(1)
    logging.info("BulidingModel!")
    Model_cons = BulidingModel(Dict)
    if "xilinx" == Dict['platform']:
        model = Model_cons.xilinx_model()
    else:
        model = Model_cons.init_model()
        #Load_weight
        model.load_weights(Dict['train_config']['pretrained_model_path'], by_name = True)

    # Freeze layers
    logging.info("Transfer learning!")
    FREEZE_LAYERS = int(round(len(model.layers)/2))
    for layer in model.layers[:FREEZE_LAYERS]:
        layer.trainable = False
        if isinstance(layer, keras.layers.BatchNormalization):
          layer.trainable = True
    for layer in model.layers[FREEZE_LAYERS:]:
        layer.trainable = True

    # Optimizer setting
    logging.info("Setting optimizer!")
    if "sgd" in Dict['train_config']['optimizer'].keys():
        optimzer_mode = Dict['train_config']['optimizer']['sgd']
        model.compile(optimizer=keras.optimizers.SGD(
                        learning_rate= optimzer_mode['lr'],
                        momentum = optimzer_mode['momentum'],
                        nesterov = optimzer_mode['nesterov']),
                        loss='categorical_crossentropy', metrics=['accuracy'])

    elif "adam" in Dict['train_config']['optimizer'].keys():
        optimzer_mode = Dict['train_config']['optimizer']['adam']
        model.compile(optimizer=keras.optimizers.Adam(
                        learning_rate= optimzer_mode['lr'],
                        epsilon = optimzer_mode['epsilon']),
                        loss='categorical_crossentropy', metrics=['accuracy'])

    # Print model layers
    logging.info(get_model_summary(model))

    # Callback setting
    callback_setting = Callback(model,
                                Dict['train_config']['lr_config']['step']['learning_rate'], 
                                Dict['train_config']['lr_config']['step']['step_size'],
                                Dict['train_config']['save_model_path'], 
                                Dict['train_config']['epochs'],
                                ).callback()

    # Training
    logging.info("Training...")
    model.fit_generator(Dataset.train_batches(),
                        steps_per_epoch = Dataset.train_batches().get_steps_per_epoch(),
                        validation_data = Dataset.valid_batches(),
                        validation_steps = Dataset.valid_batches().samples // Dict['train_config']["batch"],
                        epochs = Dict['train_config']['epochs'], verbose=0,
                        callbacks = callback_setting,
                        workers = Dict['train_config']["workers"])

    # Metrics
    logging.info("Metrics...")
    model_name = [name for name in os.listdir(Dict['train_config']['save_model_path']) if "best" in name]
    if model_name !=0:
        model = tf.keras.models.load_model(Dict['train_config']['save_model_path']+'/'+model_name[0])
        y_true, y_pred = test_summary(Dict, model)
        value = metrics_report(y_true, y_pred)

        metrics_dic = { "precision":round(value[0],2),
                        "recall":round(value[1],2),  
                        "f1_score":round(value[2],2)}
        logging.info(metrics_dic)
        # delete old metrics
        if os.path.isfile(Dict['train_config']['save_model_path']+'/'+'metrics.json'):
            os.remove(Dict['train_config']['save_model_path']+'/'+'metrics.json')
        write_json(Dict['train_config']['save_model_path']+'/'+'metrics.json', metrics_dic)

    logging.info("Ending...")
if __name__ == '__main__':
    config_logger('./training.log', 'a', "info")
    sys.exit(main() or 0)