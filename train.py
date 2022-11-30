
import argparse, sys, logging
from common.logger import config_logger
from common.utils import read_json

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
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', help = "The path of model config")
    args = parser.parse_args()
    sys.exit(main(args) or 0)