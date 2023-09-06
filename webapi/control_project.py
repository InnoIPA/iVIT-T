from flask import Blueprint, request, jsonify
from flasgger import swag_from
import logging, os, shutil, copy , time ,json ,sys ,zipfile
from datetime import datetime
from webapi import app
from webapi import socketio
from .common.utils import exists, success_msg, error_msg, read_json, regular_expression, special_words
from .common.config import PLATFORM_CFG, ROOT, YAML_MAIN_PATH ,SOCKET_LISTENERS
from .common.init_tool import get_project_info, fill_in_prjdict
from .common.database import PJ_INFO_DB,INIT_DATA,execute_db,create_table_cmd, fill_in_db, delete_data_table_cmd, update_data_table_cmd ,insert_table_cmd,insert_data_from_json ,get_project_info_cmd
from .common.inspection import Check, create_pj_dir, change_docs_prjname
from .common.upload_tool import create_class_dir, filename_processing, save_file, Upload_DB, compare_classes, add_class_filename,remove_file
from webapi.common import update_version_function
chk = Check()
app_cl_pj = Blueprint( 'control_project', __name__)
# Define API Docs path and Blue Print
YAML_PATH       = YAML_MAIN_PATH + "/control_project"

def send_Completeness(step:int,total:int,uuid:str):
    """
    This function can use socket send Completeness.

    Args:
        step (int): step now.
        total (int): total steps need to do.
        uuid (str): project uuid.
    """
    _log = "{}%".format(str(int(round((1/4)*100, 0))))
    socketio.emit(SOCKET_LISTENERS['expoet_log'], json.dumps(_log), namespace = '/{}/log'.format(uuid))

@app_cl_pj.route('/init_project', methods=['GET']) 
@swag_from("{}/{}".format(YAML_PATH, "init_project.yml"))
def init_project():
    logging.info("Get all project information!")
    # Initial_new app.config['UUID_LIST']/app.config["PROJECT_INFO"]
    app.config['UUID_LIST']={}
    app.config["PROJECT_INFO"]={}
    # Get all project info
    error_db = get_project_info()
    # Error
    if error_db:
        return error_msg(400, {}, str(error_db[1]))
    logging.info("Project:{}".format(app.config['UUID_LIST']))
    return success_msg(200, app.config["PROJECT_INFO"], "Success")

@app_cl_pj.route('/get_all_project', methods=['GET']) 
@swag_from("{}/{}".format(YAML_PATH, "get_all_project.yml"))
def get_all_project():
    logging.info("Get information from app.config['PROJECT_INFO']!")
    return success_msg(200, app.config["PROJECT_INFO"], "Success") 

@app_cl_pj.route('/get_type', methods=['GET']) 
@swag_from("{}/{}".format(YAML_PATH, "get_type.yml"))
def get_type():
    type = {"type": list(app.config['MODEL']["other"].keys())}
    return success_msg(200, type, "Success")

@app_cl_pj.route('/get_platform', methods=['GET']) 
@swag_from("{}/{}".format(YAML_PATH, "get_platform.yml"))
def get_platform():
    config = read_json(PLATFORM_CFG)
    platform = {"platform":config["platform"]}
    return success_msg(200, platform, "Success")

@app_cl_pj.route('/create_project', methods=['POST']) 
@swag_from("{}/{}".format(YAML_PATH, "create_project.yml"))
def create_project():
    pj_info_db = copy.deepcopy(PJ_INFO_DB)
    # Receive JSON and check param is/isnot None
    param = request.get_json()
    msg = chk.front_param_isnull(param)
    if msg:
        return error_msg(400, {}, "Keys:{} is not filled in.".format(msg), log=True)
    # Regular_expression
    for key in param:
        if key == "project_name" and special_words(param[key]):
            return error_msg(400, {}, "The project_name includes special characters:[{}]".format(param[key]), log=True)
        else:
            param[key] = regular_expression(param[key])
    # Create project folder and create workspace in project folder
    msg = create_pj_dir(param['project_name'])
    if msg:
        return error_msg(400, {}, str(msg), log=True)
    # Fill in dict before db 
    sample_dict = {param['project_name']:param}
    pj_info, _ = fill_in_prjdict(param['project_name'], pj_info_db, {}, sample_dict)
    # Insert to db
    error_db = fill_in_db(pj_info, 0, "project")
    if error_db:
        return error_msg(400, {}, str(error_db[1]))
    # Insert to cfg
    error_db = get_project_info()
    if error_db:
        return error_msg(400, {}, str(error_db[1]))
    # Success
    key = [k for k, v in app.config["UUID_LIST"].items() if v == param['project_name']][0]
    return success_msg(200, {}, "Success", "Create new project:[{}:{}]".format(key, param['project_name']))

@app_cl_pj.route('/<uuid>/delete_project', methods=['DELETE']) 
@swag_from("{}/{}".format(YAML_PATH, "delete_project.yml"))
def delete_project(uuid):
    # Check uuid is/isnot in app.config["PROJECT_INFO"]
    if not ( uuid in app.config["PROJECT_INFO"].keys()):
        return error_msg(400, {}, "UUID:{} does not exist.".format(uuid), log=True)
    # Get project name
    prj_name = app.config["UUID_LIST"][uuid]
    # Delete folder, app.config["PROJECT_INFO"], app.config["UUID_LIST"], database
    if os.path.isdir(ROOT + '/' + prj_name) and prj_name != "":
        # Delete data from folder
        shutil.rmtree(ROOT + '/' + prj_name)
        # Delete data from app.config
        del app.config["PROJECT_INFO"][uuid]
        del app.config["UUID_LIST"][uuid]
        # Delete data from Database
        error_db = delete_data_table_cmd("project", "project_uuid=\'{}\'".format(uuid))
        if error_db:
            return error_msg(400, {}, str(error_db[1])) 
        return success_msg(200, {}, "Success", "Deleted project:[{}:{}]".format(uuid, prj_name))
    else:
        return  error_msg(400, {}, "This project does not exist!:[{}]".format(prj_name), log=True)

@app_cl_pj.route('/<uuid>/rename_project', methods=['PUT']) 
@swag_from("{}/{}".format(YAML_PATH, "rename_project.yml"))
def rename_project(uuid):
    # Check uuid is/isnot in app.config["PROJECT_INFO"]
    if not ( uuid in app.config["PROJECT_INFO"].keys()):
        return error_msg(400, {}, "UUID:{} does not exist.".format(uuid))
    # Check key of front
    if not "new_name" in request.get_json().keys():
        return error_msg(400, {}, "KEY:new_name does not exist.")
    # Get project name
    prj_name = app.config["PROJECT_INFO"][uuid]["project_name"]
    # Get type
    type = app.config["PROJECT_INFO"][uuid]["type"]
    # Get value of front
    new_name = request.get_json()['new_name']
    if special_words(new_name) or not new_name:
        return error_msg(400, {}, "The project_name include special characters or None:[{}]".format(new_name), log=True)
    # Regular expression
    new_name = regular_expression(new_name)
    # Change app.config["PROJECT_INFO"][uuid][”project_name”] 
    app.config["PROJECT_INFO"][uuid]["project_name"] = new_name
    # Change app.config["UUID_LIST"]
    app.config["UUID_LIST"][uuid] = new_name
    # Change folder name
    main_path = ROOT + '/' + prj_name
    new_main_path = ROOT + '/' + new_name
    if not exists(main_path):
        return error_msg(400, {}, "The project does not exist:[{}]".format(prj_name), log=True)
    os.rename(main_path, new_main_path)
    # Change project name from database
    show_image_path = ""
    if exists("./project/{}/cover.jpg".format(new_name)):
        show_image_path = "/display_img/project/{}/cover.jpg".format(new_name)
    value = "project_name=\'{}\', show_image_path=\'{}\'".format(new_name, show_image_path)
    error_db = update_data_table_cmd("project", value, "project_uuid=\'{}\'".format(uuid))
    if error_db:
        return error_msg(str(error_db[1]))
    # Change project name in all iteration documents
    iter_name = [ os.path.join(new_main_path, name) for name in os.listdir(new_main_path) if name != "workspace" and os.path.isdir(os.path.join(new_main_path, name))]
    if len(iter_name) > 0:
        change_docs_prjname(iter_name, prj_name, new_name, type)
    logging.info("Renamed project:{} from {}".format(new_name, prj_name))

    return success_msg(200, request.get_json(), "Success", "Renamed project:{} from {}".format(new_name, prj_name))

@app_cl_pj.route('/export', methods=['POST']) 
@swag_from("{}/{}".format(YAML_PATH, "export.yml"))
def export_project():
    
    uuid = request.get_json()['uuid']
    package_iteration = request.get_json()['iteration']
    Check_package_iteration =[]
    error_inter=[]
    #-------------------------Step1: Check uuid is/isnot in app.config["PROJECT_INFO"]----------------------
    if not ( uuid in app.config["PROJECT_INFO"].keys()):
        return error_msg(400, {}, "UUID:{} does not exist.".format(uuid))

    #-------------------------Step2: get info from db---------------------------------

    project_name = get_project_info_cmd("project_name","project","project_uuid = '{}'".format(uuid))[0][0]
    project_table = get_project_info_cmd("*","project" ,"project_uuid = '{}'".format(uuid))
    workspace_table = get_project_info_cmd("*","workspace" ,"project_uuid = '{}'".format(uuid))
    # color_id_table = get_project_info_cmd("*","color_id" ,"project_uuid = '{}'".format(uuid))
    # unlabeled_data_table = get_project_info_cmd("unlabeled_data" , uuid)
    model_table  = []
    color_id_table = []
    iteration_table = {}

    #get iteration_table
    
    _temp_color_result=get_project_info_cmd("*","color_id" ,"project_uuid = '{}' and iteration ='{}'".format(uuid,"workspace"))
    if len(_temp_color_result)!=0:
        color_id_table.append(_temp_color_result)

    for id,iteration in enumerate(package_iteration):
        front_iter="iteration"+str(iteration)
        
        back_iter=chk.mapping_iteration(uuid, project_name, front_iter, front=True)

        if isinstance(back_iter,list):
            error_inter.append(front_iter)
            continue# example:['error', 'The itertaion does not exist in the Project:[dog_cat_classification:iteration21]'] 

    
        

        _temp_model_result=get_project_info_cmd("*","model" ,"project_uuid = '{}' and iteration ='{}'".format(uuid,back_iter.split("iteration")[1]))
        _temp_color_result=get_project_info_cmd("*","color_id" ,"project_uuid = '{}' and iteration ='{}'".format(uuid,back_iter))
        if len(_temp_model_result)==0 or len(_temp_color_result)==0:
            error_inter.append(front_iter)
            continue #example:[]

        Check_package_iteration.append(back_iter)

        model_table.append(_temp_model_result)
        color_id_table.append(_temp_color_result)
        iteration_table.update({front_iter:get_project_info_cmd("*",front_iter ,"project_uuid = '{}'".format(uuid)) })

    send_Completeness(1,4,uuid)
    #-------------------------------Step3: packeged data from db---------------------------------------------
    modify_app_config=app.config["PROJECT_INFO"][uuid].copy()   
    modify_app_config["iteration"]=len(Check_package_iteration)
    info = {
        "project":project_table,
        "workspace":workspace_table,
        "color_id":color_id_table,
        "model":model_table,
        "iteration":iteration_table,
        "config_project_info":modify_app_config,
        "config_uuid":app.config["UUID_LIST"][uuid],
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

    send_Completeness(2,4,uuid)

    #find all file in project
    Check_package_iteration.append("workspace")
    root_path= "./project/"+project_name
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

    send_Completeness(3,4,uuid)
    # paths = os.walk(r"./project/"+project_name)
    # for path , dir_lst ,file_lst in paths:
    #     for file_name in file_lst:
    #         zip_files.append(os.path.join(path,file_name))
    #Step4: Compress 
    logging.info("Compress Project: {}".format(uuid))
    with zipfile.ZipFile(zip_path, mode='w') as zf:
        for _file in zip_files:
            logging.debug('\t- Compress file: {}'.format(_file))
            zf.write(_file)
    os.chmod(zip_path, 0o777)
        # Get Size
    send_Completeness(4,4,uuid)
    os.remove(cfg_path)
    zip_size = sys.getsizeof(zip_path)
    return_info = {
        "uuid": uuid,
        "project_name": project_name,
        "cfg_name": cfg_name,
        "zip_name": zip_name,
        "zip_size": zip_size,
        "error_packege":error_inter
    }
    
    return success_msg(200,return_info, "Success")

     

@app_cl_pj.route('/import', methods=['POST']) 
@swag_from("{}/{}".format(YAML_PATH, "import.yml"))
def import_project():
    
    # parameter
    status = True #work status 

    #Step1: Check the file is not empty.
    for key in request.files.keys():
        files = request.files.getlist(key)
        if not files:
            return error_msg(400, {}, "Upload files is empty", log=True)
        
        temp_dir = "./project/temp/"
        if not os.path.exists(temp_dir):
            os.mkdir(temp_dir)

        #Step2: del all file
        for file in files:

            # Get file name 
            # example filename:dog_cat_classification_20230821 ,filename_without_Extension : dog_cat_classification
            filename ,filename_without_Extension = filename_processing(file,True)

            
            source_folder = os.path.join(temp_dir,filename_without_Extension)

            destination_folder = os.path.join("./project/",filename_without_Extension) 

            # judge project whether exist or not
            if not os.path.exists(destination_folder):
                os.mkdir(destination_folder)
            else:
                pass
                # return error_msg(400, {}, "Project rename error!")
            
            if not os.path.exists(source_folder):
                os.mkdir(source_folder)
                # Save zip
                status, filename = save_file(file, source_folder, filename)
                # Remove file size is 0 , handle save error
                if os.stat(os.path.join(source_folder,filename)).st_size == 0:
                    os.remove(os.path.join(source_folder,filename))
                    shutil.rmtree(temp_dir) 
                    shutil.rmtree(destination_folder)
                    return error_msg(400, {}, "The size of file is 0.:[{}]".format(filename), log=True)
                if status:
                #unzip file
                    with zipfile.ZipFile(os.path.join(source_folder,filename), mode='r') as zf:
                        zf.extractall(source_folder)
                    
            if status:                
                #get project info from json .
                json_filename=os.path.splitext(filename)[0]+".json"
                json_path = os.path.join(source_folder,"project/export/",json_filename)
                db_info = read_json(json_path)
                iter_map = db_info['iter_map']
                
                #refact iter_map to dict
                _temp_iter_map={}
                for id,iter in enumerate(iter_map):
                    _temp_iter_map.update({iter:id+1})

                #change iteration name (sort)
                root_path= os.path.join(source_folder,"project",filename_without_Extension)
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
                                    print(line)
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
                        os.remove(os.path.join(source_folder,filename))
                        shutil.rmtree(temp_dir) 
                        shutil.rmtree(destination_folder)
                        return error_msg(400, {}, "Change iteration name in file error!")
                
                #insert to database .
                project=db_info['project']
                uuid = project[0][0]
                status = insert_data_from_json("project",project,_temp_iter_map)
    
                if status:
                    os.remove(os.path.join(source_folder,filename))
                    shutil.rmtree(temp_dir) 
                    shutil.rmtree(destination_folder)
                    delete_data_table_cmd("project","project_uuid='"+uuid+"'")
                    return error_msg(400, {}, "Insert to DB(project) error!")
                
                workspace=db_info['workspace']
                status = insert_data_from_json("workspace",workspace,_temp_iter_map)
                if status:
                    os.remove(os.path.join(source_folder,filename))
                    shutil.rmtree(temp_dir) 
                    shutil.rmtree(destination_folder) 
                    delete_data_table_cmd("project","project_uuid='"+uuid+"'")
                    return error_msg(400, {}, "Insert to DB(workspace) error!")
                
                color_id=db_info['color_id']
                status = insert_data_from_json("color_id",color_id,_temp_iter_map)
                if status:
                    os.remove(os.path.join(source_folder,filename))
                    shutil.rmtree(temp_dir) 
                    shutil.rmtree(destination_folder)   
                    delete_data_table_cmd("project","project_uuid='"+uuid+"'")
                    return error_msg(400, {}, "Insert to DB(color_id) error!")
                
                model=db_info['model']
                status = insert_data_from_json("model",model,_temp_iter_map)
                if status:
                    os.remove(os.path.join(source_folder,filename))
                    shutil.rmtree(temp_dir) 
                    shutil.rmtree(destination_folder)
                    delete_data_table_cmd("project","project_uuid='"+uuid+"'")
                    return error_msg(400, {}, "Insert to DB(model) error!")
                
                iteration=db_info['iteration']
                for id , val in iteration.items():
                    command = create_table_cmd("iteration"+str(_temp_iter_map[id]), INIT_DATA["iteration"])
                    error_db = execute_db(command, True)
                
                    logging.warn("Created a table in the database:[{}]".format("iteration"+str(_temp_iter_map[id])))

                    status = insert_data_from_json("iteration"+str(_temp_iter_map[id]),val,_temp_iter_map)
                    if status:
                        os.remove(os.path.join(source_folder,filename))
                        shutil.rmtree(temp_dir) 
                        shutil.rmtree(destination_folder)
                        delete_data_table_cmd("project","project_uuid='"+uuid+"'")
                        return error_msg(400, {}, "Insert to DB({}) error!".format(id))
                    

                #move project from /temp ro /project
                remove_file(os.path.join(source_folder,"project",filename_without_Extension),destination_folder)


                update_version_function()

            shutil.rmtree(temp_dir) 
                

    return success_msg(200,{}, "Success")