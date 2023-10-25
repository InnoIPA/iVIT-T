import cv2, os, logging, copy, shutil, time
from .utils import exists, write_txt, read_txt, thread_pool, get_classes_list
from .config import ALLOWED_EXTENSIONS, ROOT
from .database import execute_db, update_data_table_cmd, delete_data_table_cmd ,Get_info_cmd
from .display_tool import add_color_id_db_collector, del_color_id_db

# -------------------------------------------------------------------------
# Operate bbox
def yolo2bbox(line:str, h:int, w:int):
    msg = line.split(" ")
    x1 = int(round(((float(msg[1]) - float(msg[3]) / 2) * w)))  # x_center - width/2
    y1 = int(round(((float(msg[2]) - float(msg[4]) / 2) * h)))  # y_center - height/2
    x2 = int(round(((float(msg[1]) + float(msg[3]) / 2) * w)))  # x_center + width/2
    y2 = int(round(((float(msg[2]) + float(msg[4]) / 2) * h)))  # y_center + height/2

    idx = msg[0]
    bbox = [x1, y1, x2, y2]
    return idx, bbox

def bbox2yolo(image, bbox):
    """
    YOLO format use relative coordinates for annotation
    """
    
    x0, y0, x1, y1 = bbox
    
    # x0 = float(x0)*image.shape[1]
    # y0 = float(y0)*image.shape[0]
    # x1 = float(x1)*image.shape[1]
    # y1 = float(y1)*image.shape[0]

    # print(" resize x0{} y0{} x1{} y1{} \n".format(x0, y0, x1, y1))

    xo = (x0+x1)/(2*image.shape[1])
    yo = (y0+y1)/(2*image.shape[0])
    wo = (x1-x0)/image.shape[1]
    ho = (y1-y0)/image.shape[0]

    return xo, yo, wo, ho

def img_get_classes_list(img_path:str):
    classes_name = [] 
    # get path exclude .jpg or image name
    path_split = img_path.split("/")
    if ("workspace" in path_split):
        ws_idx = path_split.index("workspace")
        txt_path = "".join( path_split[idx] + "/" for idx in range(ws_idx+1) ) + "classes.txt" 
    else:
        ds_idx = path_split.index("dataset")
        txt_path = "".join( path_split[idx] + "/" for idx in range(ds_idx+1)) + "classes.txt" 

    # append class
    if exists(txt_path):
        classes_name = get_classes_list(txt_path)
    else:
        msg = "This classes.txt does not exist in the Project:[{}]".format(txt_path)
        logging.error(msg)
        return ["error", msg]
    return classes_name

def yolo_txt_convert(uuid:str, img_path:str):
    
    frame = cv2.imread(img_path)
    img_shape = frame.shape[:2]
    classes_list = img_get_classes_list(img_path)
    if "error" in classes_list:
        return classes_list
    box_info = []
    txt_path = os.path.splitext(img_path)[0] + ".txt"
    color_info_db = get_all_color_info_db(uuid, img_path)
    # Prevent error 
    if "error" in color_info_db:
        return color_info_db
    if exists(txt_path):
        with open(txt_path, "r+") as file:
            for line in file.readlines():
                # convert
                class_id, bbox = yolo2bbox(line, img_shape[0], img_shape[1])
                # append to box_info 
                class_name = classes_list[int(class_id)]  if classes_list and len(classes_list) >= int(class_id) else '{}'.format(class_id)
                color_id = color_info_db[int(class_id)][1]
                color_hex = color_info_db[int(class_id)][2]
                box_info.append({"class_id":int(class_id), "class_name":class_name, "bbox":bbox, "color_id":color_id, "color_hex":color_hex})
    # else:
    #     msg = "This label file of the image does not exist:[{}]".format(os.path.split(txt_path)[-1])
    #     return ["error", msg]
    return img_shape, box_info

def change(do_list,idx1,indx2):
    """change list idx1 and indx2

    Args:
        do_list (list):
        idx1 (int): location of do_list.
        indx2 (int): location of do_list.

    Returns:
        list
    """
    _temp=do_list[idx1]
    do_list[idx1]=do_list[indx2]
    do_list[indx2]=_temp

    return do_list

def sort_favorite_label(uuid:str,label_id:str):
    """
    Sort 3 user most favorite label.

    Args:
        uuid (str):project uuid.
        label_id (str): label id.
    """
    #get favorite label from db
    favorite_label = Get_info_cmd("favorite_label","project","project_uuid='{}'".format(uuid))[0][0]
    
    #change turple to list
    try:
        favorite_label=list(favorite_label)
        #the same label
        if favorite_label[-1]==label_id:
            return
    except:
        favorite_label=[]
 
    #check

    if label_id in favorite_label:
        if favorite_label[0]==label_id and len(favorite_label)==3:
            #first change
            change(favorite_label,0,2)
            #2 changemp
            change(favorite_label,0,1)
        elif favorite_label[0]==label_id and len(favorite_label)==2:
            change(favorite_label,0,1)
        elif favorite_label[1]==label_id:
            change(favorite_label,1,2)
        else :
            favorite_label.append(label_id)
            if len(favorite_label)==4:
                favorite_label.pop(0)
    else:
        favorite_label.append(label_id)
        if len(favorite_label)==4:
            favorite_label.pop(0)
    # change list to str
    favorite_label=str(favorite_label)

    #insert db
    values = "favorite_label='{}'".format(favorite_label)
    select = "project_uuid='{}'".format(uuid)
    # print("DB insert  : {} \n".format(favorite_label))
    update_data_table_cmd("project",values,select)
    

def save_bbox(img_path:str, box_info:list):
    cls_idx = []
    frame = cv2.imread(img_path)

    txt_path = os.path.splitext(img_path)[0] + ".txt"

    if exists(txt_path):
        # Remove orignal file
        os.remove(txt_path)
    # Create new file


    # get all label
    img_path_split=img_path.split('/')
    img_path_split.pop()
    path_to_workspace=os.path.join(*img_path_split)
    classes_path=os.path.join(path_to_workspace,"classes.txt")
    f = open(classes_path)
    text = []
    for line in f:
        text.append(line)
    f.close()

    max_class_id=len(text)

    for val in box_info:
        bbox = val["bbox"]
        try:
            _test_class_id = int(val["class_id"])
        except:
            continue
        if _test_class_id>=max_class_id:
            continue
        # convert to yolo
        x, y, w, h = bbox2yolo(frame, bbox)
        write_txt(txt_path, "{} {:.6f} {:.6f} {:.6f} {:.6f}".format(val["class_id"], x, y, w, h))
        cls_idx.append(int(val["class_id"]))
    return cls_idx

def obj_savebbox_db(filename:str, cls_idx:list, uuid:str):
    annotate = True
    if len(cls_idx) == 0:
        annotate = False
    values = "cls_idx=\'{}\', annotate={}".format(cls_idx, annotate)
    select = "filename=\'{}\' AND project_uuid=\'{}\'".format(filename, uuid)
    # Update annotation, cls_idx in workspace of database
    error_db = update_data_table_cmd("workspace", values, select)
    logging.warn("Changed data in workspace of the database:[uuid:{}, filename:{}]".format(uuid, filename))
    if error_db:
        return error_db
    # Update nums in project of database
    error_db = label_update_pj(uuid)
    if error_db:
        return error_db
    logging.warn("Changed data in project of the database:[uuid:{}, filename:{}]".format(uuid, filename))

# -------------------------------------------------------------------------
# Get img labeling info
def get_all_color_info_db(uuid:str, path:str):
    # Get iteration
    if "workspace" in path:
        iteration = "workspace"
    else:
        iteration = "iteration" + path.split("iteration")[-1].split("/")[0]
    # Get cls_idx color_id color_hex From color_id
    command = "SELECT cls_idx, color_id, color_hex FROM color_id WHERE project_uuid=\'{}\' AND iteration=\'{}\' ORDER BY cls_idx ASC".format(uuid, iteration)
    color_info_db = execute_db(command, False)
    return color_info_db

# Get img info in classification
def cls_img_info(prj_name:str, img_path:str, color_info):
    # Get classes list in classes.txt
    img_path_split = img_path.split("/")
    classes_list = img_get_classes_list(img_path)
    if "error" in classes_list:
        return classes_list
    class_name = img_path_split[-2]
    if not class_name in classes_list:
        msg = "This class does not exist in classes.txt of the Project:[{}:{}]".format(prj_name, class_name)
        logging.error(msg)
        # return ["error", msg]
        return {}
    cls_idx = classes_list.index(class_name)
    if "workspace" == class_name or "" == class_name:
        class_name = "Unlabeled"
        info = {class_name:{"color_id":None, "color_hex":"", "class_id":None, "nums":0}}
    else:
        info = {class_name:{"color_id":color_info[int(cls_idx)][1], "color_hex":str(color_info[int(cls_idx)][2]), 
                                "class_id":int(cls_idx), "nums":1}}
    return info

# Get img info in object detection
def obj_img_info(uuid:str, img_path:str, color_info):
    class_info = {}
    bbox_info = yolo_txt_convert(uuid, img_path)
    if "error" in bbox_info:
        return bbox_info
    _ , box = bbox_info
    if len(box)==0:
        return {"Unlabeled":{"color_id":None, "color_hex":"", "class_id":None, "nums":0}}
    # Appnd to class_info
    for idx in box:
        if idx["class_name"] in class_info.keys():
            class_info[idx["class_name"]]["nums"] = class_info[idx["class_name"]]['nums']+1
        else:
            cls_idx = idx["class_id"]
            class_info[idx["class_name"]] = {"color_id":color_info[int(cls_idx)][1], "color_hex":str(color_info[int(cls_idx)][2]),
                                                "class_id":int(cls_idx), "nums":1}
    return class_info

# -------------------------------------------------------------------------
# Operate classes.txt
def add_class_txt(uuid:str, classes_path:str, class_name:str, color_id:int):
    # Check classes.txt exist
    if exists(classes_path):
        # Reading txt
        exist_cls = get_classes_list(classes_path)
        # Exist class in the classes.txt
        if class_name in exist_cls:
            msg = "This class exists in classes.txt of the Project, Can't add to the classes list:[{}]".format(class_name)
            logging.error(msg)
            return ["error", msg]
        # Remove classes.txt of exist
        os.remove(classes_path)
    else:
        exist_cls = []
    # Append new value
    if not (class_name in exist_cls):
        exist_cls.append(class_name)
        for val in exist_cls:
            write_txt(classes_path, val)
        # Append to color_id of database
        cls_color_id={str(class_name): int(color_id)}
        error_db = add_color_id_db_collector(exist_cls, uuid, "workspace", del_key=True, cls_color_id=cls_color_id)
        if error_db:
            return error_db

def del_class_txt(uuid:str, prj_name:str, type:str, main_path:str, class_name:str):
    classes_path = main_path + "/classes.txt"
    if exists(classes_path):
        # Read orignal file
        class_text = get_classes_list(classes_path)
        orignal_cls = copy.deepcopy(class_text)
        # Create orignal mapping table
        org_object = { cls:idx for idx, cls in enumerate(class_text) }
        # Remove class string
        if class_name in class_text:
            class_text.remove(class_name)
            # Remove in color_id db
            info_db = del_color_id_db(uuid, class_name, orignal_cls, class_text)
            if info_db is not None:
                return info_db
        else:
            msg = "This class does not exist in classes.txt of the Project:[{}:{}]".format(prj_name, class_name)
            logging.error(msg)
            return ["error", msg]
        # Remove orignal file
        os.remove(classes_path)
        # Writing classes.txt
        for cls in class_text:
            write_txt(classes_path, cls)
        # Create new MAP table
        new_object = { cls:idx for idx, cls in enumerate(class_text) }                
        # Delete label of all images
        if type == "object_detection":
            del_anno_index(main_path, org_object, new_object, class_name)
        return orignal_cls
    else:
        msg = "This classes.txt does not exist in the Project:[{}]".format(classes_path)
        logging.error(msg)
        return ["error", msg]

def del_anno_index(main_path:str, org_object:dict, new_object:dict, class_name:str):
    # Get all label file
    labelfile = [main_path +"/"+ name for name in os.listdir(main_path) if "classes.txt" not in name and name.split('.')[-1] in ALLOWED_EXTENSIONS["label"]]
    # All labeled remove index
    for txt in labelfile:
        # Clear ""
        val_list = [key for key in read_txt(txt).split("\n")  if key !='']
        # Remove file
        os.remove(txt)
        new_list = []
        # Update index
        for value in val_list:
            # Rearrange index
            org_idx = value.split(" ")[0]
            if not (str(org_object[class_name]) in org_idx):
                # Exchange org <-> new
                map_idx = list(org_object.values()).index(int(org_idx))
                anno = list(org_object.keys())[map_idx]
                new_idx = new_object[anno]
                value = value.replace(org_idx+" ", str(new_idx)+" ")
                new_list.append(value)

        if len(new_list) > 0:
            # Writing
            for value in new_list:
                write_txt(txt, value)

def del_class_db(uuid:str, type:str, prj_name:str, orignal_cls:list, class_name:str):
    # Get idx in orignal_cls
    if class_name in orignal_cls:
        idx = orignal_cls.index(class_name)
    else:
        msg = "This class does not exist in classes.txt of the Project:[{}:{}]".format(prj_name, class_name)
        logging.error(msg)
        return ["error", msg]
    # Get filename,cls_idx in database
    command =   """
                SELECT filename,cls_idx FROM workspace WHERE project_uuid=\'{}\' AND cls_idx::jsonb @> '[{}]'::jsonb
                """.format(uuid, idx)
    
    info_db = execute_db(command, False)
    if "error" in info_db:
        return info_db
    
    #del cls from favorite_label 

    #get favorite label from db
    favorite_label = Get_info_cmd("favorite_label","project","project_uuid='{}'".format(uuid))[0][0]
    
    #change turple to list
    try:
        favorite_label=list(favorite_label)
    except:
        favorite_label=[]
        
    if idx in favorite_label:
        favorite_label.remove(idx)
        #insert db
        values = "favorite_label='{}'".format(favorite_label)
        select = "project_uuid='{}'".format(uuid)
        # print("DB insert  : {} \n".format(favorite_label))
        update_data_table_cmd("project",values,select)
        
    
    # Forloop for change every value
    update_list = []
    for data in info_db:
        temp_dict = {"class_name":class_name, "filename":None, "cls_idx":[], "annotate":True, "project_uuid":uuid, "type":type}
        temp_dict["filename"] = data[0]
        temp_dict["cls_idx"] = list(filter(lambda val: val != idx, data[1]))
        # Length of cls_idx == 0
        if len(temp_dict["cls_idx"]) == 0:
            temp_dict["annotate"] = False
        update_list.append(temp_dict)
    # Update annotate in workspace of database
    thread_pool(del_update_ws, update_list)       
    # Update nums in project of database
    error_db = label_update_pj(uuid)
    if error_db:
        return error_db
    # Update cls_indx numbers in workspace of database
    command =   """
                UPDATE workspace
                SET cls_idx = clst.cls
                FROM  (SELECT i.filename as filename_final, array_to_json(array_agg(CASE WHEN i.idx::int>{} THEN i.idx::int-1 ELSE i.idx::int END)) AS cls FROM (SELECT filename AS filename, json_array_elements_text(cls_idx) AS idx FROM workspace WHERE project_uuid=\'{}\') AS i GROUP BY i.filename ORDER BY i.filename ASC) AS clst
                WHERE filename=clst.filename_final
                """.format(idx, uuid)
    error_db = execute_db(command, True)
    if error_db:
        return error_db

def del_update_ws(update_dict:dict):
    if update_dict["type"] == "object_detection":
        values = "cls_idx=\'{}\', annotate={}".format(update_dict["cls_idx"], update_dict["annotate"])
        select = "filename=\'{}\' AND project_uuid=\'{}\'".format(update_dict["filename"], update_dict["project_uuid"])
        # Update in database
        info_db = update_data_table_cmd("workspace", values, select)
        logging.info("Update data in workspace of the database:[uuid:{}, filename:{}]".format(update_dict["project_uuid"], update_dict["filename"]))
    elif update_dict["type"] == "classification":
        content = "img_path=\'{}\' AND project_uuid=\'{}\'".format("{}/{}".format(update_dict["class_name"],update_dict["filename"]),
                                                                                                            update_dict["project_uuid"])
        info_db = delete_data_table_cmd("workspace", content)
        logging.warn("Delete data in workspace of the database:[uuid:{}, filename:{}]".format(update_dict["project_uuid"], update_dict["filename"]))
    if info_db is not None:
        logging.error(info_db[1])
        return info_db
    time.sleep(0.5)

def label_update_pj(uuid:str):
    # Check anntation
    command =   """
                    SELECT {} FROM {} WHERE {};
                """.format("annotate",  "workspace", "project_uuid=\'{}\'".format(uuid))
    # Exclude status when data exists in DB
    info_db = execute_db(command, False)
    # Prevent error 
    if "error" in info_db:
        return info_db
    # Collect numbers
    false_num = len([ value[0] for value in info_db if value[0] == False])
    true_num = len([ value[0] for value in info_db if value[0] == True])
    # Update project
    values = "effect_img_nums={},unlabeled_img_nums={}".format(true_num, false_num)
    select = "project_uuid=\'{}\'".format(uuid)
    error_db = update_data_table_cmd("project", values, select)
    if error_db:
        return error_db
    logging.info("Update data in project of the database:[uuid:{}]".format(uuid))

# -------------------------------------------------------------------------
# Change label and mapping(classes.txt)
def cls_change_classes(uuid:str, prj_name:str, class_name:str, images_info:dict, all_stauts=False):
    # Get idx
    main_path = ROOT + '/' + prj_name + "/workspace/"
    classes_path = main_path + "classes.txt"
    # label_list = [ folder for folder in natsorted(os.listdir(main_path)) if os.path.isdir(main_path + folder)]
    classes_list = get_classes_list(classes_path)
    if class_name in classes_list:
        idx = classes_list.index(class_name)
    else:
        msg = "This class does not exist in classes.txt of the Project:[{}:{}]".format(prj_name, class_name)
        logging.error(msg)
        return ["error", msg]
    # Change file to dir of new class 
    for key in images_info.keys():
        if key == "Unlabeled":
            label = ""
        else:
            label = key
    update_list = []
    if all_stauts:
        update_list = all_change_cls(label, images_info, key, class_name, update_list, idx, uuid)
    else:
        update_list = few_change_cls(main_path, label, images_info, key, class_name, prj_name, update_list, idx, uuid)
        if "error" == update_list:
            msg = "This old class does not exist in classes.txt of the Project:[{}:{}]".format(prj_name, label)
            logging.error(msg)
            return ["error", msg]
    # Changed data in Database
    thread_pool(cls_change_update_ws, update_list)
    # Update project nums
    error_db = label_update_pj(uuid)
    if error_db:
        return error_db     
    
def all_change_cls(label:str, images_info:dict, key:str, class_name:str, update_list:list, idx:int, uuid:str):
    for value in images_info[key]:
        # Append info
        temp_dict = {"filename":value, "cls_idx":[idx], "project_uuid":uuid, "class_name":class_name, "old_cls_name":label, "annotate":True}
        update_list.append(temp_dict)
    return update_list

def few_change_cls(main_path:str, label:str, images_info:dict, key:str, class_name:str, prj_name:str, update_list:list, idx:int, uuid:str):
    if os.path.isdir(main_path + label):
        for value in images_info[key]:
            logging.warn("Moving file:[{}] to class:[{}] in Project:[{}]".format(value, class_name, prj_name))
            # Move file to destination
            if os.path.exists(main_path + label + '/' + value):
                shutil.move(main_path + label + '/' + value, 
                                main_path + class_name + '/' + value)
                # Append info
                temp_dict = {"filename":value, "cls_idx":[idx], "project_uuid":uuid, "class_name":class_name, "old_cls_name":label, "annotate":True}
                update_list.append(temp_dict)
            else:
                logging.error("This file:[{}] doesn't in Project:[{}:{}]".format(value, prj_name, key))
        return update_list
    else:
        return "error"
        
def cls_change_update_ws(update_dict:dict):
    values = "cls_idx=\'{}\', annotate={}, img_path=\'{}\'".format(update_dict["cls_idx"], update_dict["annotate"],
                                                        "{}/{}".format(update_dict["class_name"], update_dict["filename"]))
    select = "img_path=\'{}\' AND project_uuid=\'{}\'".format("{}/{}".format(update_dict["old_cls_name"],update_dict["filename"]), 
                                                                update_dict["project_uuid"])
    # Update database
    info_db = update_data_table_cmd("workspace", values, select)
    logging.warn("Changed data in workspace of the database:[uuid:{}, filename:{}]".format(update_dict["project_uuid"], update_dict["filename"]))
    if info_db is not None:
        logging.error(info_db[1])
        return info_db
    time.sleep(0.5)

def rename_cls_class(uuid:str, prj_name:str, old_class:str, class_name:str):
    main_path = ROOT + '/' + prj_name + "/workspace/"
    if exists(main_path + '/' + class_name):
        img_list = os.listdir(main_path + '/' + class_name)
        images_info = {old_class:img_list}
        error_db = cls_change_classes(uuid, prj_name, class_name, images_info, True)
        if error_db:
            return error_db
    else:
        return ["error", "This new class:[{}] does not exist in Project:[{}].".format(class_name, prj_name)]

