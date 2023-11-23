from collections.abc import Callable, Iterable, Mapping
from typing import Any
from flask import Blueprint, request, jsonify
from flasgger import swag_from
import logging, os, shutil, copy , time ,json ,sys ,zipfile,hashlib,threading ,cv2
from datetime import datetime
from webapi import app
from webapi import socketio
from webapi.common import update_version_function
from .utils import exists, success_msg, error_msg, read_json, regular_expression, special_words
from .config import PLATFORM_CFG, ROOT, YAML_MAIN_PATH ,SOCKET_LISTENERS ,EXPORT_JOSN ,IMPORT_JOSN

from .init_tool import get_project_info, fill_in_prjdict
from .database import PJ_INFO_DB,INIT_DATA,execute_db,create_table_cmd, fill_in_db, delete_data_table_cmd, update_data_table_cmd ,insert_table_cmd,insert_data_from_json ,get_project_info_cmd
from .inspection import Check, create_pj_dir, change_docs_prjname
from .upload_tool import create_class_dir, filename_processing, save_file, Upload_DB, compare_classes, add_class_filename,remove_file
from multiprocessing import Process,Queue 
chk = Check()

class CorruptedFiles(Exception):
    def __init__(self, message):
        super().__init__(message)

class Iteration_map_error(Exception):
    def __init__(self, message):
        super().__init__(message)

class insert_db_error(Exception):
    def __init__(self, message):
        super().__init__(message)

def gen_uuid():

    """
    For project rename can gen new uuid.

    Returns:
        str: new uuid , len 32.
    """
    import uuid
    new_uuid = str(uuid.uuid4())   # gen key
    new_uuid = uuid.UUID(new_uuid).hex[:32]
    return new_uuid

def remove_file(old_path:str,new_path:str):
    """
    Move all file in folder(old_path) to  new_path.

    Args:
        old_path (str): old folder path.
        new_path (str): new folder path.

    """
    filelist=os.listdir(old_path)
    for file in filelist:
        src = os.path.join(old_path,file)
        dst=os.path.join(new_path,file)
        shutil.move(src,dst)

class Process_listener(threading.Thread):
    # pass
    def __init__(self,process_dict:dict,sleep_time:int):
        self.process_dict= process_dict
        self.sleep_time = sleep_time
        threading.Thread.__init__(self)
    def run(self) :
        while True:
            del_list=[]
            if len(self.process_dict)>0:
                for uuid , val in self.process_dict.items():
                    # print("out",val["process"].communication)
                    if not val["process"].communication.empty():
                        info = val["process"].communication.get()
                        send_Completeness(info[0],info[1],info[2],info[3],info[4])
                    elif not val["process"].is_alive():
                        del_list.append(uuid)
                    
            for uuid in del_list:
                del self.process_dict[uuid]
            time.sleep(self.sleep_time)

def project_rename_handle(project_name:str,destination:str):
    """
    For project import , When project rename , change project name.
    EXAMPLE: sample -> sample(1)
    Args:
        project_name (str): project name.
    Returns:
        modify_project_name (str):Return project name after modify.
    """
    ori_project_name=project_name
    project_name=project_name+"_1"
    while(True):
        destination_folder = os.path.join(destination,project_name) 
        if not os.path.exists(destination_folder):
            return ori_project_name,project_name , destination_folder 
        project_name_iteration = int(project_name.split('_')[-1])
        project_name_iteration=project_name_iteration+1
        # project_name_no_iteration=""
        # project_name_no_iteration=ori_project_name+str(project_name_iteration)
        # for id,val in enumerate(project_name.split(')')):
        #     if id!= len(project_name.split(')'))-1 and id!= len(project_name.split(')'))-2:
        #         project_name_no_iteration=project_name_no_iteration+val+")"
            
                
            
        project_name=ori_project_name+"_"+str(project_name_iteration)

def send_Completeness(step:int,total:int,status:str,message:json,method:str):
    """
    This function can use socket send Completeness.

    Args:
        step (int): step now.
        total (int): total steps need to do.
        uuid (str): project uuid.
    """
    # print(SOCKET_LISTENERS)
    if status=="Failure":
        
        socketio.emit(SOCKET_LISTENERS[method], json.dumps(message), namespace = '/{}'.format(method))
    else:
        _log = "{}: ({}%)".format(status,str(int(round((step/total)*100, 0))))
        message.update({"message":_log})
        
        socketio.emit(SOCKET_LISTENERS[method], json.dumps(message), namespace = '/{}'.format(method))
    
    time.sleep(1)

    # socketio.emit(SOCKET_LISTENERS[method], json.dumps(), namespace = '/{}'.format(method))

class Export_Project(Process):
# class Export_Project():
    def __init__(self,uuid:str,package_iteration:list, communication:Queue,change_workspace:int=0):
        super().__init__()
        self.uuid = uuid 
        self.change_workspace = change_workspace
        self.package_iteration = package_iteration  
        self.status="Verifying"   
        self.total=3
        self.step=2
        self.communication = communication
        

    def run(self):
    # def ss(self):
        #
        try:
            prj_name = app.config["PROJECT_INFO"][self.uuid]["project_name"]
            Check_package_iteration =[]
            error_inter=[]
            self.status="Packaging"
            self.communication.put([self.step,self.total,self.status,{"data":{"project_name":prj_name}},"export"])
            # send_Completeness(self.step,self.total,self.status,{"data":{}},"export")
            #-------------------------Step2: get info from db---------------------------------

            project_name = get_project_info_cmd("project_name","project","project_uuid = '{}'".format(self.uuid))[0][0]
            project_type = get_project_info_cmd("project_type","project","project_uuid = '{}'".format(self.uuid))[0][0]
            project_table = get_project_info_cmd("*","project" ,"project_uuid = '{}'".format(self.uuid))
            if not self.change_workspace in self.package_iteration:
                workspace_table = get_project_info_cmd("*","workspace" ,"project_uuid = '{}'".format(self.uuid))
            else: 
                workspace_table=[]
                command =   """
                    SELECT {} FROM {} ;
                                """.format("max(img_serial)",  "workspace")
                    # Exclude status when data exists in DB
                info_db = execute_db(command, False)
                # print(info_db[0][0])
                max_img_serial=int(info_db[0][0])
            # color_id_table = get_project_info_cmd("*","color_id" ,"project_uuid = '{}'".format(uuid))
            # unlabeled_data_table = get_project_info_cmd("unlabeled_data" , uuid)
            model_table  = []
            color_id_table = []
            iteration_table = {}
            
            #get iteration_table
            if not self.change_workspace in self.package_iteration:

                _temp_color_result=get_project_info_cmd("*","color_id" ,"project_uuid = '{}' and iteration ='{}'".format(self.uuid,"workspace"))
                if len(_temp_color_result)!=0:
                    color_id_table.append(_temp_color_result)
            else:
                front_iter="iteration"+str(self.change_workspace)
                back_iter=chk.mapping_iteration(self.uuid, project_name, front_iter, front=True)
                _temp_color_result=get_project_info_cmd("*","color_id" ,"project_uuid = '{}' and iteration ='{}'".format(self.uuid,back_iter))
                if len(_temp_color_result)!=0:
                    _temp=[]
                    for id,val in enumerate(_temp_color_result):
                        
                        _temp.append((val[0],"workspace",val[2],val[3],val[4],val[5]))
                    color_id_table.append(_temp)

            for id,iteration in enumerate(self.package_iteration):
                deal_count=0
                front_iter="iteration"+str(iteration)
                
                back_iter=chk.mapping_iteration(self.uuid, project_name, front_iter, front=True)

                if isinstance(back_iter,list):
                    error_inter.append(front_iter)
                    continue# example:['error', 'The itertaion does not exist in the Project:[dog_cat_classification:iteration21]'] 

            
                

                _temp_model_result=get_project_info_cmd("*","model" ,"project_uuid = '{}' and iteration ='{}'".format(self.uuid,back_iter.split("iteration")[1]))
                _temp_color_result=get_project_info_cmd("*","color_id" ,"project_uuid = '{}' and iteration ='{}'".format(self.uuid,back_iter))
                if len(_temp_model_result)==0 or len(_temp_color_result)==0:
                    error_inter.append(front_iter)
                    continue #example:[]

                Check_package_iteration.append(back_iter)

                model_table.append(_temp_model_result)
                color_id_table.append(_temp_color_result)
                iteration_table.update({front_iter:get_project_info_cmd("*",front_iter ,"project_uuid = '{}'".format(self.uuid)) })
                
                if iteration == self.change_workspace:
                    #RENAME
                    _iteration_to_workspace_folder = "./project/export_temp/"+project_name+"/_temp_ws"+"/workspace"
                    _iteration_to_workspace_ori_folder="./project/export_temp/"+project_name+"/_ori_ws/workspace"
                    iteration_path = "./project/"+project_name+"/"+back_iter
                    
                    if not os.path.exists(_iteration_to_workspace_folder):
                        os.makedirs(_iteration_to_workspace_folder)
                        os.chmod(_iteration_to_workspace_folder, 0o777)

                    if not os.path.exists(_iteration_to_workspace_ori_folder):
                        os.makedirs(_iteration_to_workspace_ori_folder)
                        os.chmod(_iteration_to_workspace_ori_folder, 0o777)
                    
                    file_list = os.walk(iteration_path)
                    for path , dir_lst ,file_lst in file_list:
                        
                        for file_name in file_lst:
                            if file_name=="classes.txt" :
                                shutil.copy(path+"/"+file_name,os.path.join(_iteration_to_workspace_folder,file_name))
                            if file_name.split(".")[1] in ['png', 'jpg', 'jpeg', 'bmp','tif','tiff', 
                                                        "PNG", "JPG", "JPEG", "BMP",'TIF','TIFF']:
                                img_path= os.path.join(path,file_name)
                                
                                #check file whether exist in workspace or not
                                # file_exist_workspace = get_project_info_cmd("*","workspace","filename = '{}' \
                                #     and project_uuid='{}';".format(file_name,self.uuid))
                                # try:
                                #     workspace_create_time = get_project_info_cmd("create_time","workspace","filename = '{}' \
                                #         and project_uuid='{}';".format(file_name,self.uuid))[0][0]
                                # except:
                                #     #not exsit
                                #     workspace_create_time=0
                                # iteration_create_time= get_project_info_cmd("create_time",back_iter,"filename = '{}' \
                                #     and project_uuid='{}';".format(file_name,self.uuid))[0][0]
                                # if len(file_exist_workspace)==0 or workspace_create_time!=iteration_create_time:

                                    
                                _image= cv2.imread(img_path)
                                size =_image.shape
                                wid = size[1]
                                high = size[0]
                                max_img_serial+=1
                                _img_serial = max_img_serial
                                command ="SELECT cls_idx FROM {} where \
                                    project_uuid='{}' and filename = '{}';".format(back_iter,self.uuid,file_name)
                                _cls_idx = execute_db(command, False)[0][0]
                                
                                command ="SELECT create_time FROM {} where \
                                    project_uuid='{}' and filename = '{}';".format(back_iter,self.uuid,file_name)
                                _create_time = execute_db(command, False)[0][0]
                                if project_type=="classification":
                                    workspace_table.append([self.uuid,path.split('/')[-1]+"/"+file_name,_img_serial,file_name,high,wid,True,_cls_idx,_create_time,False])
                                elif project_type=="object_detection":
                                    workspace_table.append([self.uuid,"/"+file_name,_img_serial,file_name,high,wid,True,_cls_idx,_create_time,False])
                                
                                # else:
                                #     workspace_table.append(file_exist_workspace[0])
                                file_name_txt=file_name.split('.')[0]+".txt"
                                if project_type=="classification":
                                    cls=path.split('/')[-1]
                                    if not os.path.exists(_iteration_to_workspace_folder+"/"+cls):
                                        os.makedirs(_iteration_to_workspace_folder+"/"+cls)
                                        os.chmod(_iteration_to_workspace_folder+"/"+cls, 0o777)
                                    shutil.copy(img_path,os.path.join(_iteration_to_workspace_folder,cls,file_name)) 
                                elif project_type=="object_detection":
                                    shutil.copy(img_path,os.path.join(_iteration_to_workspace_folder,file_name)) 
                                    shutil.copy(os.path.join(path,file_name_txt),os.path.join(_iteration_to_workspace_folder,file_name_txt)) 
                                # if file_exist_workspace

                                deal_count+=1

                    # modify project_table
                    project_table = [(project_table[0][0],project_table[0][1],project_table[0][2],project_table[0][3],deal_count,\
                                      0,project_table[0][6],project_table[0][7],project_table[0][8],project_table[0][9])]
                    
                

                        
            
            
                    # print("total : ",deal_count)
                    #-------------------------------Step3: packeged data from db---------------------------------------------
            modify_app_config=app.config["PROJECT_INFO"][self.uuid].copy()   
            modify_app_config["iteration"]=len(Check_package_iteration)
            info = {
                "project":project_table,
                "workspace":workspace_table,
                "color_id":color_id_table,
                "model":model_table,
                "iteration":iteration_table,
                "config_project_info":modify_app_config,
                "config_uuid":app.config["UUID_LIST"][self.uuid],
                "iter_map":Check_package_iteration
            }
            
            #Step4: packeged info to json.
            date_time = datetime.fromtimestamp(time.time())
            str_date_time = date_time.strftime("%Y%m%d")
            file_name_formatter = lambda name, ext: f"{project_name}_{str_date_time}.{ext}"
            cfg_name = file_name_formatter(project_name, 'json')
            zip_name = file_name_formatter(project_name, 'zip')
            exp_dir = "./project/export"
            if not os.path.exists(exp_dir):
                os.mkdir(exp_dir)
                os.chmod(exp_dir, 0o777)
            cfg_path = os.path.join(exp_dir, cfg_name)
            zip_path = os.path.join(exp_dir, zip_name)
            
            zip_files = []
                # Write a Configuration
            with open(cfg_path, "w") as f:
                json.dump(info, f, indent=4)
            zip_files.append(cfg_path)

            
            #find all file in project
            Check_package_iteration.append("workspace")
            root_path= "./project/"+project_name
            if self.change_workspace in self.package_iteration:
                _iteration_to_workspace_folder = "./project/export_temp/"+project_name+"/_temp_ws"+"/workspace"
                _iteration_to_workspace_ori_folder="./project/export_temp/"+project_name+"/_ori_ws/workspace"
                remove_file(root_path+"/workspace",_iteration_to_workspace_ori_folder)
                remove_file(_iteration_to_workspace_folder,root_path+"/workspace")
                
            zip_files.append(os.path.join(root_path,"cover.jpg"))
            for iteration in os.listdir(root_path):
                if not iteration in Check_package_iteration: 
                    # print("jump iter:",iteration,'\n','\n','\n')
                    continue
                paths = os.path.join(root_path,iteration)
                file_list = os.walk(paths)
                for path , dir_lst ,file_lst in file_list:
                    for dir in dir_lst:
                        zip_files.append(os.path.join(path,dir))
                    for file_name in file_lst:
                        zip_files.append(os.path.join(path,file_name))

            
            # paths = os.walk(r"./project/"+project_name)
            # for path , dir_lst ,file_lst in paths:
            #     for file_name in file_lst:
            #         zip_files.append(os.path.join(path,file_name))
            #Step4: Compress 
            
            logging.info("Compress Project: {}".format(self.uuid))
            with zipfile.ZipFile(zip_path, mode='w') as zf:
                for _file in zip_files:
                    logging.debug('\t- Compress file: {}'.format(_file))
                    zf.write(_file)
            #move back
            if self.change_workspace in self.package_iteration:
                shutil.rmtree(root_path+"/workspace")
                if not os.path.exists(root_path+"/workspace"):
                    os.mkdir(root_path+"/workspace")
                    os.chmod(root_path+"/workspace", 0o777)
                remove_file(_iteration_to_workspace_ori_folder,root_path+"/workspace")
            check_sum = hashlib.md5(open(zip_path,'rb').read()).hexdigest()
            check_sum_path = os.path.join(exp_dir, "checksum.txt")
            check_sum_path_in_zip = os.path.join(exp_dir,"checksum.txt")
            with open(check_sum_path, "w") as f:
                f.write(check_sum+'\n')
            
            os.chdir(exp_dir)
            _temp_zip_name="./packedge_checksum"
            with zipfile.ZipFile(_temp_zip_name, mode='w') as zf:
                zf.write("./"+zip_name)
                zf.write("./checksum.txt")
            os.remove("./"+zip_name)
            os.rename(_temp_zip_name, "./"+zip_name)
            os.chmod("./"+zip_name, 0o777)
                # Get Size
            os.chdir("..")
            os.chdir("..")
            
            os.remove(cfg_path)
            os.remove(check_sum_path)
            if self.change_workspace in self.package_iteration:
                shutil.rmtree("./project/export_temp/")
            zip_size = sys.getsizeof(zip_path)
            return_info = {
                "uuid": self.uuid,
                "project_name": project_name,
                "cfg_name": cfg_name,
                "zip_name": zip_name,
                "zip_size": zip_size,
                "export_path":zip_path,
                "error_packege":error_inter,
                "check_sum":check_sum
            }
            
            self.status="Success"
            self.step=3
            self.total=3
            message={}
            message.update({"data":return_info})
            
            self.communication.put([self.step,self.total,self.status,message,"export"])
            # send_Completeness(self.step,self.total,self.status,message,"export")

        except Exception as e:
            print(e)
            message={}
            if self.change_workspace in self.package_iteration:
                shutil.rmtree("./project/export_temp/")
            message.update({"data":{
                "status":"Failure",
                "project_name":prj_name,
                "error_status":"{}: ({}%)".format(self.status,str(int(round((self.step/self.total)*100, 0)))),
                "uuid":self.uuid
            }})
            self.status="Failure"
            message.update({"message":"Failure! message:{}".format(e)})
            self.communication.put([self.step,self.total,self.status,message,"export"])
            
            
    
        
    
class Import_Project(Process):
# class Import_Project():
# class Import_Project():
    def __init__(self,task_uuid:str,deal_file:json,communication:Queue):
        super().__init__()
        self.task_uuid = task_uuid
        self.deal_file = deal_file 
        self.Flag=True        
        self.status="Importing"   
        self.total=3
        self.step=2
        self.new_project_name=""
        self.communication = communication
    def run(self):
    # def ss(self):
        try:
            self.communication.put([self.step,self.total,self.status,{"data":{}},"import"])
            # send_Completeness(self.step,self.total,self.status,{"data":{}},"import")
            uuid=""
            filename=""
            
            for order_id,file_val in self.deal_file.items():
                    
                #step6 : Verify checksum
                with zipfile.ZipFile(os.path.join(file_val["temp_dir"],file_val["filename"]), mode='r') as zf:
                        
                        zf.extractall(os.path.join(file_val["source_folder"]))
            
                check_sum_txt_path = os.path.join(file_val["source_folder"],"checksum.txt")

                
                
                #get second zip file.
                for file in os.listdir(file_val["source_folder"]):
                    if "zip" in file:
                        filename ,self.new_project_name = filename_processing(file,True)
                
                check_sum = hashlib.md5(open(os.path.join(file_val["source_folder"],filename),'rb').read()).hexdigest()
                
                with open(check_sum_txt_path) as f:
                    data = f.readline().splitlines()[0]
                    if str(check_sum)!=str(data):
                        os.remove(os.path.join(file_val["temp_dir"],file_val["filename"]))
                        shutil.rmtree(file_val["temp_dir"]) 
                        # return error_msg(400, {}, "Corrupted Files!")
                        raise CorruptedFiles("Corrupted Files!")
                  
                destination_folder = os.path.join("./project/",self.new_project_name) 

                if not os.path.exists(destination_folder):
                    os.mkdir(destination_folder)
                else:
                    file_val["rename"]=True
                    ori_project_name,self.new_project_name,destination_folder = project_rename_handle(self.new_project_name,"./project/")
                    os.mkdir(destination_folder)
                

                #step7: zipfile second
                with zipfile.ZipFile(os.path.join(file_val["source_folder"],filename), mode='r') as zf:
                    zf.extractall(os.path.join(file_val["source_folder"]))
                # print(file_val["source_folder"])
                #get project info from json .
                json_filename=os.path.splitext(filename)[0]+".json"
                json_path = os.path.join(file_val["source_folder"],"project/export/",json_filename)
                db_info = read_json(json_path)
                iter_map = db_info['iter_map']
                
                #refact iter_map to dict
                _temp_iter_map={}
                for id,iter in enumerate(iter_map):
                    _temp_iter_map.update({iter:id+1})

                #change iteration name (sort)

                # _temp_deal=file_val["ori_project_name"].split(')')
                if file_val["rename"]:
                    _t=ori_project_name
                else:
                    _t=self.new_project_name
                
                root_path= os.path.join(file_val["source_folder"],"project",_t)
                folder_list = os.listdir(root_path)
                folder_list.sort()
                for iteration in folder_list:
                    try:
                        if iteration in iter_map:

                            new_iteration="iteration"+str(_temp_iter_map[iteration]) 
                            if db_info['config_project_info']['type'] == "object_detection":
                                #modify iteration in Training.data
                                _temp={}
                                for id,line in enumerate(open(os.path.join(root_path,iteration,"Training.data"))):
                                    line=line.splitlines()[0].split("/")
                                    # print(line)
                                    _temp_item = ""
                                    for idx,item in enumerate(line):
                                        if idx==3:
                                            item=new_iteration
                                        _temp_item=_temp_item+item
                                        
                                        if idx != len(line)-1:
                                            _temp_item=_temp_item+"/"
                                    _temp.update({id:_temp_item})

                                with open(os.path.join(root_path,iteration,"Training.data"), "w") as f:
                                    for id,val in _temp.items():
                                        f.write(val+"\n")
                                root_path_json= os.path.join(root_path,iteration,"yolo"+".json")
                            else:
                                root_path_json= os.path.join(root_path,iteration,str(db_info['config_project_info']['type'])+".json")

                            model_json=read_json(root_path_json)

                            #change model json(model_path...) in iteration
                            train_dataset_path_item=model_json['train_config']['train_dataset_path'].split('/') 
                            new_train_dataset_path = os.path.join(train_dataset_path_item[0],train_dataset_path_item[1],train_dataset_path_item[2],\
                                                                    new_iteration,train_dataset_path_item[4],train_dataset_path_item[5])
                            model_json['train_config'].update({'train_dataset_path':new_train_dataset_path})
                            # example:['.', 'project', 'dog_cat_classification', 'iteration1', 'dataset', 'train']

                            val_dataset_path_item=model_json['train_config']['val_dataset_path'].split('/') 
                            new_val_dataset =os.path.join(val_dataset_path_item[0],val_dataset_path_item[1],val_dataset_path_item[2],\
                                                                    new_iteration,val_dataset_path_item[4],val_dataset_path_item[5])
                            model_json['train_config'].update({'val_dataset_path':new_val_dataset})

                            test_dataset_path_item=model_json['train_config']['test_dataset_path'].split('/') 
                            new_test_dataset_path =os.path.join(test_dataset_path_item[0],test_dataset_path_item[1],test_dataset_path_item[2],\
                                                                    new_iteration,test_dataset_path_item[4],test_dataset_path_item[5])
                            model_json['train_config'].update({'test_dataset_path':new_test_dataset_path})

                            label_path_item=model_json['train_config']['label_path'].split('/') 
                            new_label_path =os.path.join(label_path_item[0],label_path_item[1],label_path_item[2],\
                                                                    new_iteration,label_path_item[4],label_path_item[5])
                            model_json['train_config'].update({'label_path':new_label_path})

                            save_model_path_item=model_json['train_config']['save_model_path'].split('/') 
                            new_save_model_path =os.path.join(save_model_path_item[0],save_model_path_item[1],save_model_path_item[2],\
                                                                    new_iteration,save_model_path_item[4])
                            model_json['train_config'].update({'save_model_path':new_save_model_path})

                            if model_json['eval_config']['eval_dir_path']!="":
                                eval_dir_path_item=model_json['eval_config']['eval_dir_path'].split('/') 
                                new_eval_dir_path=os.path.join(eval_dir_path_item[0],eval_dir_path_item[1],eval_dir_path_item[2],\
                                                                    new_iteration,eval_dir_path_item[4],eval_dir_path_item[5])
                                model_json['eval_config'].update({'eval_dir_path':new_eval_dir_path})

                            with open(root_path_json, "w") as jsonFile:
                                json.dump(model_json, jsonFile)
                            os.chmod(root_path_json, 0o777)
                            os.rename(os.path.join(root_path,iteration),os.path.join(root_path,new_iteration))
                    except Exception as e:
                        logging.error("Change iteration name in file error: {}".format(e))
                        os.remove(os.path.join(file_val["source_folder"],file_val["filename"]))
                        shutil.rmtree(file_val["temp_dir"]) 
                        shutil.rmtree(destination_folder)
                        # return error_msg(400, {}, "Change iteration name in file error!")
                        raise Iteration_map_error("Change iteration name in file error!")
                #insert to database .
                project=db_info['project']
                uuid = project[0][0]
                
                if file_val["rename"]:
                    new_uuid= gen_uuid()
                    uuid=new_uuid
                else:
                    new_uuid=""
                
                status = insert_data_from_json("project",project,_temp_iter_map,file_val["rename"],self.new_project_name,new_uuid,file_val["source_folder"])

                if status:
                    os.remove(os.path.join(file_val["source_folder"],file_val["filename"]))
                    shutil.rmtree(file_val["temp_dir"]) 
                    shutil.rmtree(destination_folder)
                    delete_data_table_cmd("project","project_uuid='"+uuid+"'")
                    # return error_msg(400, {}, "Insert to DB(project) error!")
                    raise insert_db_error("Insert to DB(project) error!")
                workspace=db_info['workspace']
                status = insert_data_from_json("workspace",workspace,_temp_iter_map,file_val["rename"],self.new_project_name,new_uuid,file_val["source_folder"])
                
                if status:
                    os.remove(os.path.join(file_val["source_folder"],file_val["filename"]))
                    shutil.rmtree(file_val["temp_dir"]) 
                    shutil.rmtree(destination_folder) 
                    delete_data_table_cmd("project","project_uuid='"+uuid+"'")
                    # return error_msg(400, {}, "Insert to DB(workspace) error!")
                    raise insert_db_error("Insert to DB(workspace) error!")
                color_id=db_info['color_id']
                status = insert_data_from_json("color_id",color_id,_temp_iter_map,file_val["rename"],self.new_project_name,new_uuid,file_val["source_folder"])
                if status:
                    os.remove(os.path.join(file_val["source_folder"],file_val["filename"]))
                    shutil.rmtree(file_val["temp_dir"]) 
                    shutil.rmtree(destination_folder)   
                    delete_data_table_cmd("project","project_uuid='"+uuid+"'")
                    # return error_msg(400, {}, "Insert to DB(color_id) error!")
                    raise insert_db_error("Insert to DB(color_id) error!")
                model=db_info['model']
                status = insert_data_from_json("model",model,_temp_iter_map,file_val["rename"],self.new_project_name,new_uuid,file_val["source_folder"])
                if status:
                    os.remove(os.path.join(file_val["source_folder"],file_val["filename"]))
                    shutil.rmtree(file_val["temp_dir"]) 
                    shutil.rmtree(destination_folder)
                    delete_data_table_cmd("project","project_uuid='"+uuid+"'")
                    # return error_msg(400, {}, "Insert to DB(model) error!")
                    raise insert_db_error("Insert to DB(model) error!")
                iteration=db_info['iteration']
                for id , val in iteration.items():
                    command = create_table_cmd("iteration"+str(_temp_iter_map[id]), INIT_DATA["iteration"])
                    error_db = execute_db(command, True)
                
                    logging.warn("Created a table in the database:[{}]".format("iteration"+str(_temp_iter_map[id])))

                    status = insert_data_from_json("iteration"+str(_temp_iter_map[id]),val,_temp_iter_map,file_val["rename"],self.new_project_name,new_uuid,file_val["source_folder"])
                    if status:
                        os.remove(os.path.join(file_val["source_folder"],file_val["filename"]))
                        shutil.rmtree(file_val["temp_dir"]) 
                        shutil.rmtree(destination_folder)
                        delete_data_table_cmd("project","project_uuid='"+uuid+"'")
                        # return error_msg(400, {}, "Insert to DB({}) error!".format(id))
                        raise insert_db_error("Insert to DB({}) error!".format(id))
                
                #move project from /temp ro /project
                # print(_t)
                # print(os.path.join(file_val["source_folder"],"project",_t),file_val["destination_folder"])
                remove_file(root_path,destination_folder)


                update_version_function()

                shutil.rmtree(file_val["temp_dir"]) 
            
            return_info = {
                "task_uuid":self.task_uuid,
                "project_uuid": uuid,
                "project_name": self.new_project_name
            }
            
            self.status="Success"
            self.step=3
            self.total=3
            message={}
            message.update({"data":return_info})
            self.communication.put([self.step,self.total,self.status,message,"import"])
            # send_Completeness(self.step,self.total,self.status,message,"import")           
        except Exception as e:
            try:
                os.remove(os.path.join(file_val["source_folder"],file_val["filename"]))
            except:
                pass
            try:
                shutil.rmtree(file_val["temp_dir"]) 
            except:
                pass
            try:
                shutil.rmtree(destination_folder)
            except:
                pass
            try:
                delete_data_table_cmd("project","project_uuid='"+uuid+"'")
            except:
                pass
            
            message={}
            # print(e)
            message.update({"data":{
                
                "status":"Failure",
                "uuid":self.task_uuid,
                "error_status":"{}: ({}%)".format(self.status,str(int(round((self.step/self.total)*100, 0)))),
                
            }})
            message.update({"message":"Failure! message:{}".format(e)})
            self.status ="Failure"
            self.communication.put([self.step,self.total,self.status,message,"import"])
            # send_Completeness(self.step,self.total,self.status,message,"import")
