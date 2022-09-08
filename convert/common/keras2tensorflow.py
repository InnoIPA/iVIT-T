#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, sys, argparse, logging
from keras2tensorflow_api import convert_main

import logging
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[2]/"common"))
from logger import config_logger

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input_model', required=True, type=str, help='Path to the input model.')
    parser.add_argument('--input_model_json', required=False, type=str, help='Path to the input model architecture in json format.')
    parser.add_argument('--input_model_yaml', required=False, type=str, help='Path to the input model architecture in yaml format.')
    parser.add_argument('--output_model', required=True, type=str, help='Path where the converted model will be stored.')

    parser.add_argument('--save_graph_def', default=False, action="store_true", help='Whether to save the graphdef.pbtxt file which contains the graph definition in ASCII format. default=%(default)s')
    parser.add_argument('--output_nodes_prefix', required=False, type=str, help='If set, the output nodes will be renamed to `output_nodes_prefix`+i, where `i` will numerate the number of of output nodes of the network.')
    parser.add_argument('--quantize', default=False, action="store_true", help='If set, the resultant TensorFlow graph weights will be converted from float into eight-bit equivalents. See documentation here: https://github.com/tensorflow/tensorflow/tree/master/tensorflow/tools/graph_transforms. default=%(default)s')
    parser.add_argument('--channels_first', default=False, action="store_true", help='Whether channels are the first dimension of a tensor. The default is TensorFlow behaviour where channels are the last dimension. default=%(default)s')
    parser.add_argument('--output_meta_ckpt', default=False, action="store_true", help='If set to True, exports the model as .meta, .index, and .data files, with a checkpoint file. These can be later loaded in TensorFlow to continue training. default=%(default)s')

    args = parser.parse_args()

    convert_main(args)


if __name__ == '__main__':
    config_logger('./convert.log', 'a', "info")
    main()
