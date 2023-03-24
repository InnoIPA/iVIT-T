import sys, logging
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
        logging.info('Get metrics of classification...')
        from classification import Classification
        # Initial
        cls = Classification(dictionary)
        # Get metrics of model
        cls.metrics()

    elif 'yolo' in args.config:
        logging.info('Get metrics of yolo...')
        from objectdetection.yolo import Yolo
        # Initial
        yolo = Yolo(dictionary)
        # Get metrics of model
        yolo.metrics()

    elif 'unet' in args.config:
        logging.info('Get metrics of unet...')
        pass

    elif 'vae' in args.config:
        logging.info('Get metrics of vae...')
        pass
    
    else:
        logging.info('The name of json is wrong...')

if __name__ == '__main__':
    config_logger('./metrics.log', 'w', "info")
    args = build_argparser().parse_args()
    sys.exit(main(args) or 0)