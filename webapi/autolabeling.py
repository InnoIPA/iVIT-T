from flask import Blueprint, request, jsonify
from flasgger import swag_from
from webapi import app
from .common.utils import error_msg, success_msg
from .common.config import ROOT, YAML_MAIN_PATH, EVAL_VAL,AUTOLABEL_VAL,MICRO_SERVICE
from .common.inspection import Check
from .common.evaluate_tool import Evaluate, threshold_process, temp_label_data_db 
from .common.database import delete_data_table_cmd , get_unlabeled_img_path_cmd ,get_project_info_cmd , get_img_serial_db,Get_info_cmd,execute_db
from .common.gpu_memory import cal_gpu_memory

import time,os,requests,json,socket ,copy
from multiprocessing import Process ,Queue
import subprocess
from ivit.micro_service_tool.micro_service_fastapi import app_run
from .common.labeling_tool import get_all_color_info_db,get_classes_list
chk = Check()

app_auto_labeling = Blueprint( 'autolabeling', __name__)
# Define API Docs path and Blue Print
YAML_PATH       = YAML_MAIN_PATH + "/autolabeling"

def _assign_port():
    """
        Get number of free port (start from 6531).
    Returns:
        int: number of free port.
    """
    port=6531
    while(True):
        if _check_port(port):
            return port
        else:
            port+=1
   
def _check_port(port:int):
    """
    To check port status.
    Args:
        port(int):
    Returns:
        status(bool):True:status of port is free ; falsestatus of port is not free .
    """
    
    s = socket.socket()
    try:
        s.connect(("localhost", port))
        return False
    except:
        return True
    finally:
        s.close()

@app_auto_labeling.route('/<uuid>/autolabeling', methods=['POST'])
@swag_from("{}/{}".format(YAML_PATH, "load_model.yml"))
def load_model(uuid):
    #init parameter
    
    iter = request.get_json()['iteration']
    prj_name = get_project_info_cmd("project_name","project","project_uuid='{}'".format(uuid))[0][0]
    task_type = get_project_info_cmd("project_type","project","project_uuid='{}'".format(uuid))[0][0]
    try:
        iter=MICRO_SERVICE[uuid]["iteration"][0]
    except:
        get_model_nums_command="select model_nums from project where project_uuid='{}';".format(uuid)
        model_num=execute_db(get_model_nums_command,False)[0][0]
        iter="iteration"+str(model_num)
    try:
        threshold=MICRO_SERVICE[uuid]["threshold"]
    except:
        threshold=0.7
    start=time.time()
    get_load_model_status=False
    # _comunication_q=queue.Queue()
    #check the project wether already run autolabel or not 
    try:
        
        if MICRO_SERVICE[uuid]["process"]:
            return success_msg(200, {} , "Success", "Model is exist!:[{}:{}]".format(prj_name, MICRO_SERVICE[uuid]["iteration"]))
    except:
        pass
    

    #check this project have best model
    try:
        iter=MICRO_SERVICE[uuid]["iteration"][0]
        dir_iteration=MICRO_SERVICE[uuid]["iteration"][1]
        
    except:
        try:
            dir_iteration = chk.mapping_iteration(uuid, prj_name, iter, front=True)
        except:
            return error_msg(400, {}, str(dir_iteration[1]), log=True)


    if not (uuid in MICRO_SERVICE.keys()):
        MICRO_SERVICE.update({
            uuid:{
                "iteration":[iter,dir_iteration],
                "threshold":threshold,
            }

        })
    # check gpu wether is enough or not
    gpu=cal_gpu_memory()
    free_gpu_memory = gpu.now()
    if free_gpu_memory < 2: 
        return error_msg(400, {}, "GPU Memory is not enough to do autolabeling!")

    


    
    #try load model

    #get path of model json 
    if task_type == "object_detection":
        dictionary = ROOT + '/' +prj_name+'/'+ dir_iteration + '/'+ "yolo" + '.json'
    else:
        dictionary = ROOT + '/' +prj_name+'/'+ dir_iteration + '/'+ task_type + '.json'

    #get free port
    port=_assign_port()
    try:
        start_time=time.time()
        command = "python3 ./ivit/micro_service_tool/micro_service_fastapi.py \
                                          -t {}\
                                          -d {}\
                                          -p {}\
                                          ".format(task_type,dictionary,port)
        
        micro_server = subprocess.Popen(command.split(), stdout=subprocess.PIPE, text=True)

        while(get_load_model_status==False):
            # z=""
            for line in micro_server.stdout:
                if "success" in line.strip():
                    get_load_model_status=True
                    break
                elif "failed" in line.strip():
                    return error_msg(400, {}, "load model error!")        
            
        # time.sleep(10)
        print('\n',"load model time: ",(time.time()-start_time),'\n')
        MICRO_SERVICE.update({
            uuid:{
                "process":micro_server,
                "iteration":[iter,dir_iteration],
                "threshold":threshold,
                "create_time":time.time(),
                "port":port
                }
                })
    except Exception as e:
        return error_msg(400, {}, "load model error! {}".format(e))
    
    
    return success_msg(200, {"model":MICRO_SERVICE[uuid]['iteration'][0],"threshold":MICRO_SERVICE[uuid]['threshold']} , "Success", "Success load model:[{}:{}]".format(prj_name, iter))

@app_auto_labeling.route('/<uuid>/autolabeling', methods=['GET'])
@swag_from("{}/{}".format(YAML_PATH, "get_autolabel_parameter.yml"))
def get_autolabel_parameter(uuid):
    
    if not (uuid in MICRO_SERVICE.keys()):
        prj_name = get_project_info_cmd("project_name","project","project_uuid='{}'".format(uuid))[0][0]
        get_model_nums_command="select model_nums from project where project_uuid='{}';".format(uuid)
        
        model_num=execute_db(get_model_nums_command,False)[0][0]
        iter="iteration"+str(model_num)
        dir_iteration=""
        try:
            dir_iteration = chk.mapping_iteration(uuid, prj_name, iter, front=True)
        except:
            return error_msg(400, {}, str(dir_iteration), log=True)
        MICRO_SERVICE.update({
            uuid:{
                "iteration":[iter,dir_iteration],
                "threshold":0.7,
            }

        })
    info={
        "iteration":MICRO_SERVICE[uuid]['iteration'][0],
        "threshold":MICRO_SERVICE[uuid]['threshold']

    }
    return success_msg(200, info , "Success", "Get autolabel info,threshold={},iteration={}".format(MICRO_SERVICE[uuid]['iteration'][0],\
                                                                                                    MICRO_SERVICE[uuid]['threshold']))

@app_auto_labeling.route('/<uuid>/autolabeling', methods=['PUT'])
@swag_from("{}/{}".format(YAML_PATH, "modify_autolabel_parameter.yml"))
def modify_autolabel_parameter(uuid):
    
    #init parameter
    iter = request.get_json()['iteration']
    threshold = request.get_json()['threshold']
    prj_name = get_project_info_cmd("project_name","project","project_uuid='{}'".format(uuid))[0][0]
    task_type = get_project_info_cmd("project_type","project","project_uuid='{}'".format(uuid))[0][0]
    try:
        dir_iteration = chk.mapping_iteration(uuid, prj_name, iter, front=True)
    except:
        return error_msg(400, {}, "{} Not exist!".format(iter), log=True)
    

    if not (uuid in MICRO_SERVICE.keys()):
        MICRO_SERVICE.update({
            uuid:{
                "iteration":[iter,dir_iteration],
                "threshold":threshold,
            }

        })
    if not MICRO_SERVICE[uuid].__contains__("process"):
        MICRO_SERVICE.update({
            uuid:{
                "iteration":[iter,dir_iteration],
                "threshold":threshold,
            }

        })
        return success_msg(200, {} , "Success", "Setting iter: {} , threshold:{}.".format(MICRO_SERVICE[uuid]['iteration'][0]\
                                                                                                  ,MICRO_SERVICE[uuid]['threshold']))
    # _comunication_q=Queue(maxsize=5)
    get_load_model_status=False
    old_iter = MICRO_SERVICE[uuid]['iteration']
    old_thres = MICRO_SERVICE[uuid]['threshold']
    #check this project have this iteration


    
    
    #if change iter will load new model 
    print(old_iter,iter," now",'\n')
    if old_iter[0]!=iter:
        #reload model
        #release
        try:
            MICRO_SERVICE[uuid]["process"].kill()
            MICRO_SERVICE[uuid]["process"].wait()
            del MICRO_SERVICE[uuid]["process"]
        except:
            return error_msg(400, {},"Release autolabeling model error!")
        
        if not (uuid in MICRO_SERVICE.keys()):
            MICRO_SERVICE.update({
                uuid:{
                    "iteration":[iter,dir_iteration],
                    "threshold":threshold,
                }

            })
        # check gpu wether is enough or not
        gpu=cal_gpu_memory()
        free_gpu_memory = gpu.now()
        if free_gpu_memory < 2: 
            return error_msg(400, {}, "GPU Memory is not enough to do autolabeling!")

        #try load model
        #get path of model json 
        if task_type == "object_detection":
            dictionary = ROOT + '/' +prj_name+'/'+ dir_iteration + '/'+ "yolo" + '.json'
        else:
            dictionary = ROOT + '/' +prj_name+'/'+ dir_iteration + '/'+ task_type + '.json'

        #get free port
        port=_assign_port()
        try:
            start_time=time.time()
            command = "python3 ./ivit/micro_service_tool/micro_service_fastapi.py \
                                          -t {}\
                                          -d {}\
                                          -p {}\
                                          ".format(task_type,dictionary,port)
            micro_server = subprocess.Popen(command.split(), stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
            
            micro_server = subprocess.Popen(command.split(), stdout=subprocess.PIPE, text=True)

            while(get_load_model_status==False):
                # z=""
                for line in micro_server.stdout:
                    if "success" in line.strip():
                        get_load_model_status=True
                        break
                    elif "failed" in line.strip():
                        return error_msg(400, {}, "load model error!")   
            # while(_comunication_q.get()=="success"):
            #     break
            # time.sleep(10)
            print('\n',"load model time: ",(time.time()-start_time),'\n')
            MICRO_SERVICE.update({
                uuid:{
                    "process":micro_server,
                    "iteration":[iter,dir_iteration],
                    "threshold":threshold,
                    "create_time":time.time(),
                    "port":port
                    }
                    })
        except Exception as e:
            return error_msg(400, {}, "load model error! {}".format(e))
        
    else:
        MICRO_SERVICE[uuid]['threshold']=threshold

    #change all confirm status
                
    change_confirm_status_command = "update workspace set confirm='false' where project_uuid='{}';".format(uuid)
    execute_db(change_confirm_status_command,True)

    return success_msg(200, {} , "Success", "Change iter: {} to {} , threshold: {} to {}.".format(old_iter[0],MICRO_SERVICE[uuid]['iteration'][0]\
                                                                                                  ,old_thres,MICRO_SERVICE[uuid]['threshold']))

@app_auto_labeling.route('/<uuid>/autolabeling/infer', methods=['POST'])
@swag_from("{}/{}".format(YAML_PATH, "autolabeling_infer.yml"))
def autolabeling_infer(uuid):
    #parameter init
    if not MICRO_SERVICE.__contains__(uuid):
        return error_msg(400, {}, "project {} not load model yet.".format(uuid))
    try:
        port=MICRO_SERVICE[uuid]["port"]
    except:
        return error_msg(400, {}, "Do autolabeling error! No load Model!")
    auto_label_url = 'http://localhost:'+str(port)+'/upload_auto_label'
    payload ={}
    threshold=0.7
    img_path=""
    # judge img exist or not
    prj_name = get_project_info_cmd("project_name","project","project_uuid='{}'".format(uuid))[0][0]
    img_name = request.get_json()['img_name']
    info_db = get_img_serial_db(uuid, img_name)
    

    if "error" in info_db:
        return error_msg(400, {}, info_db)
    elif info_db[0] == None:
        msg = "This image is labeled or does not exist in the Project:[{}:{}]".format(prj_name, img_name)
        return error_msg(400, {}, msg)
    _img=get_project_info_cmd("img_path","workspace","project_uuid='{}' and img_serial='{}'".format(uuid,info_db[0][0]))[0][0]
    img_path = img_path+ROOT+"/"+prj_name+"/"+"workspace"+"/"+_img

    # print("img item root:{} , pro:{} , img_path:{} , _img:{}".format(ROOT,prj_name,img_path,_img))
    #judge unlabeled_data wether have value or not
    # try:
    _temp_unlabeled_data =get_project_info_cmd("*","unlabeled_data","img_serial='{}' and project_uuid='{}'".format(info_db[0][0],uuid))
    if not len(_temp_unlabeled_data)==0:
        return success_msg(200, {} , "Success", "{} already finish autolabeling".format(img_name))
    # except:
    #     pass
    
    
    
    temp_dict = {}
    payload.update({'img_path':img_path})

    # payload2 = json.dumps(payload)
    try: 
        x = requests.post(auto_label_url,json=payload)
    except:
        return error_msg(400, {}, " File: {} , Do autolabeling error! ".format(img_name))
    if x.status_code == 200:
        # print("sucessfully fetched the data! data info = {} .".format(x.json()))
        
        
        temp_dict.update({img_name:x.json()[0]})

        EVAL_VAL[uuid] = temp_dict
        
        log_dict = threshold_process(uuid, prj_name, threshold)
        error_db = temp_label_data_db(uuid, prj_name, log_dict)
        if error_db:
            return error_msg(400, {}, error_db[1])
        
    else:

        return error_msg(400, {}, " File: {} , Do autolabeling error! status = {}".format(img_name,x.status_code))
    # write pridect info to db

    return success_msg(200, {} , "Success", "Auto labeling for unlabeled images in the Project:[{}:{}]".format(prj_name, img_name))

@app_auto_labeling.route('/<uuid>/autolabeling', methods=['DELETE'])
@swag_from("{}/{}".format(YAML_PATH, "release_model.yml"))
def release_model(uuid):
    if not MICRO_SERVICE.__contains__(uuid):
        return error_msg(400, {}, "project {} not load model yet.".format(uuid))
    

    try:
        MICRO_SERVICE[uuid]["process"].kill()
        MICRO_SERVICE[uuid]["process"].wait()
        del MICRO_SERVICE[uuid]["process"]
        print("******************************************",'\n')
        print(MICRO_SERVICE[uuid],'\n')
        print("******************************************",'\n')
        
    except Exception as e:
        return error_msg(400, {},"Release autolabeling model error! {}".format(e))
    

    # Get project name
    prj_name = app.config["PROJECT_INFO"][uuid]["project_name"]
    error_db = delete_data_table_cmd("unlabeled_data", "project_uuid=\'{}\'".format(uuid))
    if error_db:
        return error_msg(400, {}, str(error_db[1]))

    return success_msg(200, {} , "Success", "Release autolabeling model!")


@app_auto_labeling.route('/<uuid>/clear_autolabeling', methods=['GET'])
@swag_from("{}/{}".format(YAML_PATH, "clear_autolabeling.yml"))
def clear_autolabeling(uuid):
    # Check uuid is/isnot in app.config["PROJECT_INFO"]
    if not ( uuid in app.config["PROJECT_INFO"].keys()):
        return error_msg(400, {}, "UUID:{} does not exist.".format(uuid), log=True)
    # Get project name
    prj_name = app.config["PROJECT_INFO"][uuid]["project_name"]
    # Clear
    error_db = delete_data_table_cmd("unlabeled_data", "project_uuid=\'{}\'".format(uuid))
    if error_db:
        return error_msg(400, {}, str(error_db[1]))
    return success_msg(200, {}, "Success", "Clear temp data of autolabeling in the Project:[{}]".format(prj_name))


@app_auto_labeling.route('/<uuid>/favorite_label', methods=['GET'])
@swag_from("{}/{}".format(YAML_PATH, "favorite_label.yml"))
def favorite_label(uuid):
    #init parameter 
    prj_name = get_project_info_cmd("project_name","project","project_uuid='{}'".format(uuid))[0][0]
    class_txt=os.path.join("./project",prj_name,"workspace","classes.txt")
    color_info_db = get_all_color_info_db(uuid,"workspace")
    if os.path.isfile(class_txt):
        class_name = get_classes_list(class_txt)
    else:
        return error_msg(400, {}, "This project {} , not label yet!".format(uuid))
    try:
        favorite_label = Get_info_cmd("favorite_label","project","project_uuid='{}'".format(uuid))[0][0]
    except Exception as e:
        return error_msg(400, {}, "Get favorite label from db error ! {}".format(e))
    
    try:
        favorite_label=list(favorite_label)
    except:
        favorite_label=[]
    _temp_json={}
    #refact
    for idx,val in enumerate(favorite_label):
        
        # print("val:{} , favorite_label:{} \n".format(val,favorite_label))
        # print("class_name:{} \n".format(class_name))
        # print("color_info_db:{} \n".format(color_info_db))
        
        _temp_json.update({
            (idx+1):{
                "class_id":val,
                "class_name":class_name[val],
                "class_color":color_info_db[val][2]
            }

        })

    # print(_temp_json)

    return success_msg(200, _temp_json, "Success", "Get favorite label in the Project:[{}]".format(uuid))
@app_auto_labeling.route('/<uuid>/confirm_status', methods=['POST'])
@swag_from("{}/{}".format(YAML_PATH, "confirm_status.yml"))
def confirm_status(uuid):
    image_name = request.get_json()['image_name']
    get_confirm_status_command="select confirm from workspace where project_uuid='{}' \
        and  img_path='{}';".format(uuid,"/"+image_name)
    get_confirm_status_info=execute_db(get_confirm_status_command,False)[0][0]

    return success_msg(200, {image_name:get_confirm_status_info}, "Success", "Get {} confirm status {} in the Project:[{}]".format(image_name,get_confirm_status_info,uuid))
# @app_auto_labeling.route('/<uuid>/autolabeling', methods=['POST'])
# @swag_from("{}/{}".format(YAML_PATH, "autolabeling.yml"))
# def autolabeling(uuid):
#     #check gpu wether is enough or not
#     gpu=cal_gpu_memory()
#     free_gpu_memory = gpu.now()
#     if free_gpu_memory < 2: 
#         return error_msg(400, {}, "GPU Memory is not enough to do autolabeling!")
#     eval = Evaluate()
#     # Check uuid is/isnot in app.config["PROJECT_INFO"]
#     if not ( uuid in app.config["PROJECT_INFO"].keys()):
#         return error_msg(400, {}, "UUID:{} does not exist.".format(uuid), log=True)
#     # Check key of front
#     if not "iteration" in request.get_json().keys():
#         return error_msg(400, {}, "KEY:iteration does not exist.", log=True)
#     if not "img_key" in request.get_json().keys():
#         return error_msg(400, {}, "KEY:img_key does not exist.", log=True)
#     # Get project name
#     prj_name = app.config["PROJECT_INFO"][uuid]["project_name"]
#     # Get type
#     type = app.config["PROJECT_INFO"][uuid]["type"]
#     # Get value of front
#     front_iteration = request.get_json()['iteration']
#     img_key = request.get_json()['img_key']
#     # Mapping iteration
#     dir_iteration = chk.mapping_iteration(uuid, prj_name, front_iteration, front=True)
#     if "error" in dir_iteration:
#         return error_msg(400, {}, str(dir_iteration[1]), log=True)
#     # Get model.json
#     if type == "object_detection":
#         model = "yolo"
#     elif type == "classification":
#         model = type

#     #get project name
#     project_name = get_project_info_cmd("project_name","project","project_uuid ='{}'".format(uuid))
    
#     #combine img path
#     root_path = "./project/"+project_name[0][0]+"/workspace"

#     #get path of unlabeled img  from table where not do autolabeling
#     raw_img_path = get_unlabeled_img_path_cmd(uuid)

#     #deal raw data example:[('/a.jpg',), ('/cover.jpg',), ('/8.jpg',), ('/4.jpg',), ('/12.jpg',), ('/13.jpg',)]
#     if len(raw_img_path)>1:
#         for id ,val in enumerate(raw_img_path):
            
#             AUTOLABEL_VAL.append(root_path+val[0])
#     else:
#         return success_msg(200, {}, "Success", "Clear temp data of autolabeling in the Project:[{}]".format(prj_name))
#     img_key ="custom"
    
#     # Setting evaluate.json
#     msg = eval.set_eval_json(prj_name, dir_iteration, model, autokey=True, img_key=img_key)
#     if msg:
#         return error_msg(400, {}, "{}:[{}:{}]".format(msg, prj_name, front_iteration))
#     # Evaluate
#     command = "python3 adapter.py -c {} --eval --autolabel_upload".format(ROOT + '/' +prj_name+'/'+ dir_iteration + '/'+ model + '.json')
#     # Run command
#     eval.thread_eval(uuid, type, command)
#     result = eval.cmd_q.get()
#     if "Error" in result.keys():
#         return error_msg(400, result["Error"], "Out of memory", log=True)
#     EVAL_VAL[uuid] = result
#     # Threshold / Rearrange
#     threshold = 0
#     log_dict = threshold_process(uuid, prj_name, threshold)
#     # Save database
#     error_db = temp_label_data_db(uuid, prj_name, log_dict)
#     if error_db:
#         return error_msg(400, {}, error_db[1])
#     return success_msg(200, {}, "Success", "Auto labeling for unlabeled images in the Project:[{}:{}]".format(prj_name, img_key))