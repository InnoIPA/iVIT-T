# Basic
import logging,sys,json,os
from argparse import ArgumentParser

#main module
# from .micro_service_tool.eval_cls import Eval_classfication
# from .micro_service_tool.eval_yolo import Eval_yolo

# Fastapi
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
# from flask import Flask, request, jsonify

MODEL={}

app = FastAPI()

class Item(BaseModel):
    img_path: str

 # @app.route('/upload_auto_label', methods=['POST']) 
@app.post('/upload_auto_label')
def evalute(item: Item):


    
    img_path = "/workspace/project/fruit_object_detection/workspace/apple_1.jpg"
            
    if img_path ==None:
        return (400, {}, "micro service (evalute) error! {}".format("Can't find img!"))

    global MODEL
    result = MODEL["MODEL"].evaluate_with_path(item.img_path)

    return result,200

# @app.route('/', methods=["GET"])
@app.get('/')
def home():
    return "check evalute can run!", 200

def read_json(path:str):
    with open(path) as f:
        return json.load(f)

def build_argparser():
    parser = ArgumentParser(add_help=False)
    args = parser.add_argument_group('Options')
    args.add_argument('-t', '--t', required=True, help = "model_type")
    args.add_argument('-d', '--d', required=True, help = "model_path")
    return parser

def app_run(type,config,port,queue):
    logging.info("upload...")
    # app = Flask(__name__)
    
    # Create initial table in db
    warm_img=os.path.join(config.split('/')[0],config.split('/')[1],config.split('/')[2],"cover.jpg",)
    dictionary = read_json(config)
    global MODEL
    try:
        if type=="classification":
            from .eval_cls import Eval_classfication
            
            model = Eval_classfication(dictionary)
           
            
            result = model.evaluate_with_path(warm_img)
            # print(result)
            MODEL["MODEL"]=model
            queue.put("success")
        
            #     print(app.config)
        elif type=="object_detection":
            
            from .eval_yolo import Eval_yolo
            
            
            model = Eval_yolo(dictionary)
            MODEL["MODEL"]=model
            queue.put("success")

        uvicorn.run(
        app, 
        host = '0.0.0.0', 
        port = port,
        workers = 1 )

    except Exception as e:
        queue.put("failed")
        logging.error(400, {}, "load model error! {}".format(e))

    
    
    # app.run(
    #     host='0.0.0.0', 
    #     port=6531)

if __name__ == '__main__':
    # Create log
    port=6531
    type= "classification"
    dictionary ="/workspace/project/dog_cat_classification/iteration1/classification.json" 
    app_run(type,dictionary,port)