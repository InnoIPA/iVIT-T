#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import argparse,sys
from keras2onnx_api import convert_main
import logging
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[2]/"common"))
from logger import config_logger

def main():
    parser = argparse.ArgumentParser(argument_default=argparse.SUPPRESS)
    parser.add_argument('--keras_model_file', required=True, type=str, help='path to keras model file')
    parser.add_argument('--output_file', required=True, type=str, help='output onnx model file')
    parser.add_argument('--op_set', required=False, type=int, help='onnx op set, default=%(default)s', default=10)
    parser.add_argument('--inputs_as_nchw', help="convert input layout to NCHW", default=False, action="store_true")
    parser.add_argument('--with_savedmodel', default=False, action="store_true", help='use a temp savedmodel for convert')
    args = parser.parse_args()
    convert_main(args)

if __name__ == '__main__':
    # config_logger('./convert.log', 'a', "info")
    main()

