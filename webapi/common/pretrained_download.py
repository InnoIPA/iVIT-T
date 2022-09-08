import gdown
import argparse
import wget

yolofile = ['yolov3.conv.81', 'yolov3-tiny.conv.15', 'yolov4.conv.137']

# Initial Argparse
parser = argparse.ArgumentParser()
path = './pretrainedmodel'
parser.add_argument("-arch", "--arch", help="The name of arch")
parser.add_argument("-application", "--application", help="The name of application")
args = parser.parse_args()

if args.application == "classification":

        if '_' in args.arch and not 'mobilenet' in args.arch:
            archdir = args.arch.split('_')[0] + args.arch.split('_')[1]
        else:
            archdir = args.arch
        url = 'https://api.ngc.nvidia.com/v2/models/nvidia/tao/pretrained_classification/versions/'+archdir+'/files/'+args.arch+'.hdf5'

        wget.download(url, path + '/'+args.arch+'.hdf5')
       
elif args.application == "yolo":
    GDRIVE_URL = "https://drive.google.com/uc?export=download&id="
    if 'yolov4-tiny' in args.arch:
        
        url = '{}1SPJtVPqtwKVEjo5hBGM4B9ClJLv6OcBO'.format(GDRIVE_URL)
        gdown.download(url, path + '/yolov4-tiny.conv.29')  

    else:

        if args.arch == 'yolov3':
            url = '{}1JYKlw2N7E0toGsaDZnrqAlIIAjwU_aem'.format(GDRIVE_URL)
            gdown.download(url, path + '/' +yolofile[0])

        elif args.arch == 'yolov3-tiny':
            url = '{}1N3aVDgvgt13ZNjps-tr_9UvT88uEf7GA'.format(GDRIVE_URL)
            gdown.download(url, path + '/' +yolofile[1]) 

        elif 'yolov4' in args.arch:
            url = '{}18OmCm91sVzS3ijf3apkGPa1lncRxsndn'.format(GDRIVE_URL)
            gdown.download(url, path + '/' +yolofile[2]) 