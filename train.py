import sys, logging, os
from argparse import ArgumentParser, SUPPRESS
from common.logger import config_logger
from common.utils import read_json

def build_argparser():
    parser = ArgumentParser(add_help=False)
    args = parser.add_argument_group('Options')
    args.add_argument('-h', '--help', action='help', default=SUPPRESS, help='Show this help message and exit.')
    args.add_argument('-c', '--config', required=True, help = "The path of model config")
    return parser

def main(args):
    dictionary = read_json(args.config)
    if 'classification' in args.config:
        logging.info('Start training of classification...')
        from classification import Classification
        # Initial
        cls = Classification(dictionary)
        # Training model
        cls.train()

    elif 'yolo' in args.config:
        logging.info('Start training of yolo...')
        from objectdetection.yolo import Yolo
        # Initial
        yolo = Yolo(dictionary)
        # Training model
        yolo.train()
        # Delete generated files
        remove_list = ["anchors.txt", "counters_per_class.txt", "bad.list", 
                       "chart_yolov3-tiny.png", "chart_yolov4-tiny.png", "chart_yolov4.png",
                       "chart_yolov4-leaky.png", "chart.png"]
        for key in remove_list:
            if os.path.isfile(key):
                os.remove(key)

    elif 'unet' in args.config:
        logging.info('Start training of unet...')
        pass

    elif 'vae' in args.config:
        logging.info('Start training of vae...')
        pass
    
    else:
        logging.info('The name of json is wrong...')

if __name__ == '__main__':
    config_logger('./training.log', 'w', "info")
    args = build_argparser().parse_args()
    sys.exit(main(args) or 0)