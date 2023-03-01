import logging, os

def check_model(path:str, filetype:str):
    # Check model is exist
    if os.path.exists(path):
        logging.info('-----The {} is converted.'.format(filetype))
    else:
        logging.error('-----The {} fails to convert.'.format(filetype))