import gdown, wget, sys, os
from argparse import ArgumentParser, SUPPRESS
import multiprocessing as mp

YOLOFILE = ['yolov3.conv.81', 'yolov3-tiny.conv.15', 'yolov4.conv.137']
YOLOARCH = ["yolov3-tiny", "yolov4", "yolov4-tiny"]
CLSARCH = ["resnet_18", "resnet_50", "vgg_16"]
PATH = './pretrainedmodel'

def build_argparser():
    parser = ArgumentParser(add_help=False)
    args = parser.add_argument_group('Options')
    args.add_argument('-h', '--help', action='help', default=SUPPRESS, help='Show this help message and exit.')
    args.add_argument("-arch", "--arch", help="The name of arch")
    args.add_argument("-application", "--application", help="The name of application")
    args.add_argument("-all", "--all", action="store_true", help="Download all pre-trained model")
    return parser

# Create this bar_progress method which is invoked automatically from wget
def bar_progress(current, total, width=80):
    progress_message = "Downloading: %d%% [%d / %d] bytes" % (current / total * 100, current, total)
    print(progress_message)
    # Don't use print() as it will print in new line every time.
    # sys.stdout.write("\r" + progress_message)
    # sys.stdout.flush()
    
def cls_pretrained(arch, all=False):
    if '_' in arch and not 'mobilenet' in arch:
        archdir = arch.split('_')[0] + arch.split('_')[1]
    else:
        archdir = arch
    url = 'https://api.ngc.nvidia.com/v2/models/nvidia/tao/pretrained_classification/versions/'+archdir+'/files/'+arch+'.hdf5'
    
    if not (os.path.exists(PATH + "/" + arch + '.hdf5')):
        if all:
            wget.download(url, PATH + '/'+arch+'.hdf5')
        else:
            wget.download(url, PATH + '/'+arch+'.hdf5', bar=bar_progress)
    else:
        print("This model has existed:[ {} ]".format(arch))

def yolo_pretrained(arch):
    GDRIVE_URL = "https://drive.google.com/uc?export=download&id="

    if 'yolov4-tiny' in arch:
        url = '{}1sFXs_yL9s52M6---qPhdHY0FVfCi_i6e'.format(GDRIVE_URL)
        if not (os.path.exists(PATH + '/yolov4-tiny.conv.29')):
            gdown.download(url, PATH + '/yolov4-tiny.conv.29')  
        else:
            print("This model has existed:[ {} ]".format(arch))

    else:
        if arch == 'yolov3':
            url = '{}17qLQ4BCDj61P4RD2zqBU90D3ndqBrE_a'.format(GDRIVE_URL)
            if not (os.path.exists(PATH + '/' +YOLOFILE[0])):
                gdown.download(url, PATH + '/' +YOLOFILE[0])
            else:
                print("This model has existed:[ {} ]".format(arch))

        elif arch == 'yolov3-tiny':
            url = '{}1HJSXmnAqywUHFiMBfQjE5PhFHXvHAkmb'.format(GDRIVE_URL)
            if not (os.path.exists(PATH + '/' +YOLOFILE[1])):
                gdown.download(url, PATH + '/' +YOLOFILE[1]) 
            else:
                print("This model has existed:[ {} ]".format(arch))

        elif 'yolov4' in arch:
            url = '{}1p3DgT43gxdcYSI76xU8YFSYalOiYGW6d{}'.format(GDRIVE_URL, "&confirm=t")
            if not (os.path.exists(PATH + '/' +YOLOFILE[2])):
                gdown.download(url, PATH + '/' +YOLOFILE[2]) 
            else:
                print("This model has existed:[ {} ]".format(arch))

def download_model(arch):
    if arch in CLSARCH:
        cls_pretrained(arch, True)
    else:
        yolo_pretrained(arch)

def main(args):
    if args.all:
        # Extend list
        extend_model = []
        extend_model.extend(YOLOARCH)
        extend_model.extend(CLSARCH)
        # Download
        pool_obj = mp.Pool(7)
        pool_obj.map(download_model, extend_model)
        
    elif args.application == "classification":
        arch = args.arch
        cls_pretrained(arch)

    elif args.application == "yolo":
        arch = args.arch
        yolo_pretrained(arch)

    else:
        print("The Parser is null.")

if __name__ == '__main__':
    args = build_argparser().parse_args()
    sys.exit(main(args) or 0)