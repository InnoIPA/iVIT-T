import sys
from argparse import ArgumentParser, SUPPRESS
from ivit import training, metrics, eval, converting

def build_argparser():
    parser = ArgumentParser(add_help=False)
    args = parser.add_argument_group('Options')
    args.add_argument('-h', '--help', action='help', default=SUPPRESS, help='Show this help message and exit.')
    args.add_argument('-c', '--config', required=True, help = "The path of model config")
    args.add_argument('--train', default=False, action='store_true', help = "Training a model.")
    args.add_argument('--metrics', default=False, action='store_true', help = "Evaluating performance metrics.")
    args.add_argument('--eval', default=False, action='store_true', help = "Validating the model.")
    args.add_argument('--convert', default=False, action='store_true', help = "Converting the model.")
    args.add_argument('--autolabel_upload', default=False, action='store_true', help = "For upload to do autolabeling.")
    return parser

def main(args):
    # Training
    if args.train:
        training(args.config)
    # Get_metrics
    if args.metrics:
        metrics(args.config)
    # Evaluating
    if args.eval:
        eval(args.config,args.autolabel_upload)
    # Converting
    if args.convert:
        converting(args.config)

if __name__ == '__main__':
    args = build_argparser().parse_args()
    sys.exit(main(args) or 0)