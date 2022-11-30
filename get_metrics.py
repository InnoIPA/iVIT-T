
import argparse, sys, logging
from common.logger import config_logger
from common.utils import read_json

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
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', help = "The path of model config")
    args = parser.parse_args()
    sys.exit(main(args) or 0)