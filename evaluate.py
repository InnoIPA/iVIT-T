import sys
import logging
from common.logger import config_logger 
from common.utils import read_json 
from evaluate.eval_classification import Eval_classfication
from evaluate.eval_yolo import Eval_yolo

def main():
    dict = read_json("./Project/samples/Config.json")
    
    if "classification" in dict['model_json']:
        logging.info('Start classification evaluate...')
        # initial model
        eval_cls = Eval_classfication()
        # eval model
        eval_cls.evalate()
        
    elif "yolo" in dict['model_json']:
        logging.info('Start yolo evaluate...')
        # initial model
        eval_yolo = Eval_yolo()
        # eval model
        eval_yolo.evalate()

if __name__ == '__main__':
    config_logger('./evaluate.log', 'w', "info")
    sys.exit(main() or 0)