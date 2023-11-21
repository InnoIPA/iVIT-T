from flask import Blueprint, request, jsonify
from flasgger import swag_from
import logging, os, shutil, copy , time ,json ,sys ,zipfile , threading , hashlib,uuid
from datetime import datetime
from webapi import app
from webapi import socketio
from .common.utils import exists, success_msg, error_msg, read_json, regular_expression, special_words
from .common.config import PLATFORM_CFG, ROOT, YAML_MAIN_PATH ,SOCKET_LISTENERS ,EXPORT_JOSN ,IMPORT_JOSN
from .common.init_tool import get_project_info, fill_in_prjdict
from .common.database import PJ_INFO_DB,INIT_DATA,execute_db,create_table_cmd, fill_in_db, delete_data_table_cmd, update_data_table_cmd ,insert_table_cmd,insert_data_from_json ,get_project_info_cmd
from .common.inspection import Check, create_pj_dir, change_docs_prjname
from .common.upload_tool import create_class_dir, filename_processing, save_file, Upload_DB, compare_classes, add_class_filename,remove_file
from .common.export_project_tool import Export_Project,Import_Project,Process_listener ,send_Completeness
from webapi.common import update_version_function
from multiprocessing import Process,Queue
chk = Check()
export_listener = Process_listener(EXPORT_JOSN,1)
export_listener.start()

import_listener = Process_listener(IMPORT_JOSN,1)
import_listener.start()

app_cl_pj = Blueprint( 'control_project', __name__)
# Define API Docs path and Blue Print
YAML_PATH       = YAML_MAIN_PATH + "/control_project"


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

@app_cl_pj.route('/<uuid>/autolabel_status', methods=['GET']) 
@swag_from("{}/{}".format(YAML_PATH, "autolabel_status_get.yml"))
def autolabel_status_get(uuid):
    if not ( uuid in app.config["PROJECT_INFO"].keys()):
        return error_msg(400, {}, "UUID:{} does not exist.".format(uuid))
    try:
        auto_status = app.config["PROJECT_INFO"][uuid]["on_autolabeling"]
    except:
        auto_status=False
        app.config["PROJECT_INFO"][uuid].update({"on_autolabeling":auto_status})
    return success_msg(200, {"autolabel_status":auto_status}, "Success", "Get project:{},autolabeling status:{} ".format(uuid,auto_status))

@app_cl_pj.route('/<uuid>/autolabel_status', methods=['POST']) 
@swag_from("{}/{}".format(YAML_PATH, "autolabel_status_post.yml"))
def autolabel_status_post(uuid):
    if not ( uuid in app.config["PROJECT_INFO"].keys()):
        return error_msg(400, {}, "UUID:{} does not exist.".format(uuid))
    app.config["PROJECT_INFO"][uuid]["on_autolabeling"] = not app.config["PROJECT_INFO"][uuid]["on_autolabeling"]
    return success_msg(200, {}, "Success", "Change project:{},autolabeling status:{} ".format(uuid, app.config["PROJECT_INFO"][uuid]["on_autolabeling"]))

# def cmd(uuid,package_iteration):
#     p = Process(target=export_project, args=(uuid,package_iteration, ))
#     p.start()

def func(x): 
    while True: 
        for i in x:
            print(i,'\n') 
            time.sleep(1)

@app_cl_pj.route('/export', methods=['POST']) 
@swag_from("{}/{}".format(YAML_PATH, "export.yml"))
def export():
    
    data={"data":{}}
    send_Completeness(0,3,"Waiting",data,"export")
    if not "uuid" in request.get_json().keys():
        return error_msg(500, {}, "KEY:uuid does not exist.")
    uuid = request.get_json()['uuid']
    change_workspace = request.get_json()['change_workspace']
    send_Completeness(1,3,"Verifying",data,"export")
    
    # print("OUT: ", id(socketio))

    #-------------------------Step1: Check uuid is/isnot in app.config["PROJECT_INFO"]----------------------
    if not ( uuid in app.config["PROJECT_INFO"].keys()):
        return error_msg(500, {}, "UUID:{} does not exist.".format(uuid))
    
    if EXPORT_JOSN.__contains__(uuid):
        return error_msg(500, {}, "UUID:{} do export now!".format(uuid))
    package_iteration = request.get_json()['iteration']
    # export_project(uuid,package_iteration)
    communicate=Queue()
    export_process = Export_Project(uuid,package_iteration,communicate ,change_workspace)
    export_process.start()
    # export_process.ss()
    
    EXPORT_JOSN.update({
        uuid:{
        "create_time":time.time(),
        "process":export_process
                        }}) 
    
    return success_msg(200,{}, "Success")

@app_cl_pj.route('/stop_export', methods=['POST']) 
@swag_from("{}/{}".format(YAML_PATH, "stop_export.yml"))
def stop_export():
    if not "uuid" in request.get_json().keys():
        return error_msg(400, {}, " Export uuid not exist!")
    uuid = request.get_json()['uuid']
 
    try:
        time.sleep(2)
        EXPORT_JOSN[uuid]["process"].terminate()
        EXPORT_JOSN[uuid]["process"].join() 
        del EXPORT_JOSN[uuid]
        return success_msg(200,{}, "Success")
    except Exception as e :
        return error_msg(400, {}, "Export project release error! {}".format(e))
     
def project_rename_handle(project_name:str,sourse:str,destination:str):
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
            return ori_project_name,project_name , destination_folder , os.path.join(sourse,project_name)
        project_name_iteration = int(project_name.split('_')[-1])
        project_name_iteration=project_name_iteration+1
        # project_name_no_iteration=""
        # project_name_no_iteration=ori_project_name+str(project_name_iteration)
        # for id,val in enumerate(project_name.split(')')):
        #     if id!= len(project_name.split(')'))-1 and id!= len(project_name.split(')'))-2:
        #         project_name_no_iteration=project_name_no_iteration+val+")"
            
                
            
        project_name=ori_project_name+"_"+str(project_name_iteration)
        
        
    


@app_cl_pj.route('/import', methods=['POST']) 
@swag_from("{}/{}".format(YAML_PATH, "import.yml"))
def import_pj():
    data={"data":{}}
    send_Completeness(0,3,"Waiting",data,"import")
    import_uuid = str(uuid.uuid4())[:8]
    # parameter
    deal_file={}
    order_id=0
    rename=False
    ori_project_name=""
    #Step1: Get all upload zip file
    
    send_Completeness(1,3,"Verifying",data,"import")
    for key in request.files.keys():
        files = request.files.getlist(key)

        #step2 : create ./project/temp/ to deal upload zip file
        temp_dir = "./project/temp/"
        if not os.path.exists(temp_dir):
            os.mkdir(temp_dir)
        
        #step3: save all upload zip file into ./project/temp/
        for file in files:
            # Get file name 
            # example filename:dog_cat_classification_20230821 ,filename_without_Extension : dog_cat_classification
            filename ,filename_without_Extension = filename_processing(file,True)
            source_folder = os.path.join(temp_dir,filename_without_Extension)
            destination_folder = os.path.join("./project/",filename_without_Extension) 

            #step4 : if project is exist in ivit-t create project in ./project
            if not os.path.exists(destination_folder):
                os.mkdir(destination_folder)
            else:
                rename=True
                ori_project_name,filename_without_Extension,destination_folder,source_folder = project_rename_handle(filename_without_Extension,temp_dir,"./project/")
                
                os.mkdir(destination_folder)
                
            if not os.path.exists(source_folder):
                os.mkdir(source_folder)
            #step5 : Save zip
                status, filename = save_file(file, temp_dir, filename)
                deal_file.update({order_id:{
                                    "filename":filename,
                                    "filename_without_Extension":filename_without_Extension,
                                    "ori_project_name":ori_project_name,
                                    "source_folder":source_folder,
                                    "destination_folder":destination_folder,
                                    "temp_dir":"./project/temp/",
                                    "rename":rename
                }})
                order_id=order_id+1
    
    # print(deal_file)
    # print(rename)
    # print(ss)
    # return error_msg(400, {}, "Project rename error!")
    communicate=Queue()
    import_process = Import_Project(import_uuid,deal_file,communicate)
    # Start thread
    # import_process.ss()
    import_process.start()
    IMPORT_JOSN.update({
        import_uuid:{
        "create_time":time.time(),
        "process":import_process
                        }})      

    return success_msg(200,{"import_uuid":import_uuid}, "Success")

@app_cl_pj.route('/stop_import', methods=['POST']) 
@swag_from("{}/{}".format(YAML_PATH, "stop_import.yml"))
def stop_import():
    if not "import_uuid" in request.get_json().keys():
        return error_msg(400, {}, " import_uuid not exist!")
    import_uuid = request.get_json()['import_uuid']
    try:
        # IMPORT_JOSN[import_uuid]["thread"].setFlag(False) 
        time.sleep(2)
        IMPORT_JOSN[uuid]["process"].terminate()
        IMPORT_JOSN[uuid]["process"].join() 
        del IMPORT_JOSN[import_uuid]
        return success_msg(200,{}, "Success")
    except:
        return error_msg(400, {}, "Import project release error!!")

@app_cl_pj.route('/get_export_process', methods=['GET']) 
@swag_from("{}/{}".format(YAML_PATH, "get_export_process.yml"))
def get_export_process():
    _temp=[]
    for uuid , val in EXPORT_JOSN.items():
        _temp.append(uuid)
    return success_msg(200,{"process":_temp}, "Success")

@app_cl_pj.route('/get_import_process', methods=['GET']) 
@swag_from("{}/{}".format(YAML_PATH, "get_import_process.yml"))
def get_import_process():
    _temp=[]
    for uuid , val in IMPORT_JOSN.items():
        _temp.append(uuid)
    return success_msg(200,{"process":_temp}, "Success")