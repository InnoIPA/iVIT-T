import argparse, sys, logging
from common.logger import config_logger 
from common.utils import read_json 

def main(args):
    dictionary = read_json(args.config)

    if 'classification' in args.config:
        logging.info('Start evaluating classification ...')
        from classification import Eval_classfication
        # initial model
        eval_cls = Eval_classfication(dictionary)
        # eval model
        eval_cls.evalate()
        
    elif 'yolo' in args.config:
        logging.info('Start evaluating yolo...')
        from objectdetection.yolo import Eval_yolo
        # initial model
        eval_yolo = Eval_yolo(dictionary)
        # eval model
        eval_yolo.evalate()

if __name__ == '__main__':
    config_logger('./evaluate.log', 'w', "info")
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', help = "The path of model config")
    args = parser.parse_args()
    sys.exit(main(args) or 0)