#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import argparse
import sys, logging

from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[2]/"common"))
from logger import config_logger

from darknet2keras_api import convert_main

parser = argparse.ArgumentParser(description='Darknet To Keras Converter.')
parser.add_argument('config_path', help='Path to Darknet cfg file.')
parser.add_argument('weights_path', help='Path to Darknet weights file.')
parser.add_argument('output_path', help='Path to output Keras model file.')
parser.add_argument(
    '-p',
    '--plot_model',
    help='Plot generated Keras model and save as image.',
    action='store_true')
parser.add_argument(
    '-w',
    '--weights_only',
    help='Save as Keras weights file instead of model file.',
    action='store_true')
parser.add_argument(
    '-f',
    '--fixed_input_shape',
    help='Use fixed input shape specified in cfg.',
    action='store_true')
parser.add_argument(
    '-r',
    '--yolo4_reorder',
    help='Reorder output tensors for YOLOv4 cfg and weights file.',
    action='store_true')

if __name__ == '__main__':
    # config_logger('./convert.log', 'a', "info")
    convert_main(parser.parse_args())
