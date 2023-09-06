import os, logging, cv2, sys
import numpy as np
import tensorflow as tf
from tensorflow.python.eager.context import eager_mode
from PIL import Image
from hailo_sdk_client import ClientRunner
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[2] / 'common'))
from utils import ALLOWED_EXTENSIONS

def preproc(image, type, output_height=224, output_width=224, resize_side=256):
    ''' imagenet-standard: aspect-preserving resize to 256px smaller-side, then central-crop to 224px'''
    if "classification" == type:
        with eager_mode():
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            h, w = image.shape[0], image.shape[1]
            scale = tf.cond(tf.less(h, w), lambda: resize_side / h, lambda: resize_side / w)
            resized_image = tf.compat.v1.image.resize_bilinear(tf.expand_dims(image, 0), [int(h*scale), int(w*scale)])
            cropped_image = tf.compat.v1.image.resize_with_crop_or_pad(resized_image, output_height, output_width)
            return tf.squeeze(cropped_image)
    else:
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        resized_image = cv2.resize(image, (output_width, output_height), cv2.INTER_LINEAR)
        return tf.squeeze(resized_image)
    
def get_img_list(path:str, type:str):
    if "classification" == type:
        folder_list = [ os.path.join(path, dir) for dir in os.listdir(path)]
        img_list = []
        for images_path in folder_list:
            images_list = [ os.path.join(images_path, img_name) for img_name in os.listdir(images_path) 
                                    if img_name.split(".")[-1] in ALLOWED_EXTENSIONS["image"]]
            img_list.extend(images_list)
    elif "object_detection" == type or "segmentation" == type:
        if "segmentation" == type:
            path = os.path.join( path, "images")
        img_list = [ os.path.join(path, img_name) for img_name in os.listdir(path) if img_name.split(".")[-1] in ALLOWED_EXTENSIONS["image"]]
    return img_list

class Hailo:
    def __init__(self, model_name:str, path:str, type:str, shape:list):
        self.model_name = model_name
        self.model_path = path
        self.main_path = os.path.split(path)[0]
        self.type = type
        self.shape = shape
        self.iteration = self.main_path.split(model_name + '/')[-1].split("/")[0]

    def parsing(self, start_node:list, end_node:list):
        runner = ClientRunner(hw_arch='hailo8')
        if "classification" == self.type or "segmentation" == self.type:
            runner.translate_tf_model(self.model_path, self.model_name, start_node_names=start_node, end_node_names=end_node)
        elif "object_detection" == self.type:
            runner.translate_onnx_model(self.model_path, self.model_name, start_node_names=start_node, end_node_names=end_node, 
                                                                                net_input_shapes={'input':[1, self.shape[2], self.shape[0], self.shape[1]]})

        self.hailo_model_har_name = '{}_hailo_model.har'.format(self.model_name)
        self.hailo_model_har_path = os.path.join(self.main_path, self.hailo_model_har_name)
        runner.save_har( self.hailo_model_har_path )

    
    def optimization(self):
        runner = ClientRunner(hw_arch='hailo8', har_path= self.hailo_model_har_path)
        img_path = './project/{}/{}/dataset/val'.format(self.model_name, self.iteration)
        img_list = get_img_list(img_path, self.type)
        # Length limit
        if len(img_list) < 10:
            img_path = './project/{}/{}/dataset/train'.format(self.model_name, self.iteration)
            img_list = get_img_list(img_path, self.type)
        logging.warn("Quantize image nums:{}".format(len(img_list)))
        self.quantized_model_har_path = '{}_quantized_model.har'.format(self.model_name)

        calib_dataset = np.zeros((len(img_list), self.shape[0], self.shape[1], self.shape[2]), dtype=np.float32)
        shape = self.shape[0] if self.shape[0] < self.shape[1] else self.shape[1]
        for idx, img_path in enumerate(sorted(img_list)):
            img = np.array(Image.open(img_path))
            img_preproc = preproc(img, self.type, self.shape[0], self.shape[1], shape)
            calib_dataset[idx,:,:,:] = img_preproc.numpy().astype(np.uint8)

        if "classification" == self.type:
            alls_lines = [
                # 'normalization1 = normalization([123.675, 116.28, 103.53], [58.395, 57.12, 57.375])\n',
                'normalization1 = normalization([103.53, 116.28, 123.675], [1., 1., 1.])\n',
                'model_optimization_config(calibration, batch_size=2)\n',  # Batch size is 8 by default
            ]
        elif "object_detection" == self.type:
            alls_lines = [
                'normalization1 = normalization([0.0, 0.0, 0.0], [255.0, 255.0, 255.0])\n',
                'model_optimization_config(calibration, batch_size=2)\n',  # Batch size is 8 by default
            ]
        elif "segmentation" == self.type:
            alls_lines = [
                'normalization1 = normalization([127.5, 127.5, 127.5], [127.5, 127.5, 127.5])\n',
                'model_optimization_config(calibration, batch_size=2)\n',  # Batch size is 8 by default
            ]

        # Save the commands in an .alls file, this is the Model Script
        simple_script = self.main_path + "/simple_script.alls"
        open(simple_script,'w').writelines(alls_lines)
        # Load the model script to ClientRunner so it will be considered on optimization
        runner.load_model_script(simple_script)
        # For a single input layer, could use the shorter version - just pass the dataset to the function
        # runner.optimize(calib_dataset)
        # For multiple input nodes, the calibration dataset could also be a dictionary with the format:
        # {input_layer_name_1_from_hn: layer_1_calib_dataset, input_layer_name_2_from_hn: layer_2_calib_dataset}
        hn_layers = runner.get_hn_dict()['layers']
        logging.warn([layer for layer in hn_layers if hn_layers[layer]['type'] == 'input_layer']) # See available input layer names
        calib_dataset_dict = {'{}/input_layer1'.format(self.model_name): calib_dataset} # In our case there is only one input layer
        runner.optimize(calib_dataset_dict)
        self.hailo_model_q_har_path = os.path.join(self.main_path, self.quantized_model_har_path)
        runner.save_har(self.hailo_model_q_har_path)

    def compile(self):
        runner = ClientRunner(hw_arch='hailo8', har_path= self.hailo_model_q_har_path)
        # For Mini PCIe modules or Hailo-8R devices, use hw_arch='hailo8r'
        hef = runner.compile()

        file_name = os.path.join(self.main_path, self.model_name + '.hef')
        with open(file_name, 'wb') as f:
            f.write(hef)
        har_path = '{}_compiled_model.har'.format(self.model_name)
        runner.save_har( os.path.join(self.main_path, har_path) )


