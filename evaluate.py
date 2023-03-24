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
        logging.info('Start evaluating classification ...')
        from classification import Eval_classfication
        # initial model
        eval_cls = Eval_classfication(dictionary)
        # eval model
        eval_cls.evaluate()
        
    elif 'yolo' in args.config:
        logging.info('Start evaluating yolo...')
        from objectdetection.yolo import Eval_yolo
        # initial model
        eval_yolo = Eval_yolo(dictionary)
        # eval model
        eval_yolo.evaluate()

if __name__ == '__main__':
    config_logger('./evaluate.log', 'w', "info")
    args = build_argparser().parse_args()
    sys.exit(main(args) or 0)