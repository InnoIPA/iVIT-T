import logging, os, copy, shutil, random, threading, string, time, glob
from werkzeug.utils import secure_filename
from natsort import natsorted
from .utils import exists, read_txt, thread_pool, get_classes_list
from .config import ROOT, ALLOWED_EXTENSIONS
from .init_tool import cls_fill_in_wsdict, obj_fill_in_wsdict, read_color_table_db
from .database import execute_db, update_data_table_cmd, WS_INFO_DB, fill_in_db
from .display_tool import create_classes, get_cls_max_db, add_color_id_db_collector
from .labeling_tool import add_class_txt
from .utils import regular_expression
# import concurrent.futures
lock = threading.RLock()


def remove_file(old_path, new_path):
    filelist = os.listdir(old_path) 
    for file in filelist:
        src = os.path.join(old_path, file)
        dst = os.path.join(new_path, file)
        shutil.move(src, dst)

def create_class_dir(key:str, prj_name:str, type:str):
    # Setting save path
    if key == "Unlabeled" or type == "object_detection":
        dirs = ""
    else:
        dirs = regular_expression(key)

    dir_path = ROOT + '/' + prj_name + "/workspace/" + dirs
    # Create target Directory
    try:
        os.makedirs(dir_path, exist_ok=True, mode=0o777)
    except Exception as exc:
        logging.warn(exc)
        pass
    
    return dirs, dir_path

def filename_processing(file:str,is_import:bool):
    """
    get file name from path.

    Args:
        file (str): path to file.
        is_import (bool): wether use in import or not.

    Returns:
        str: if use in import will retrun file name without Filename Extension.
             if use in upload will retrun file name with Filename Extension.
    """
    # Get file name
    filename = file.filename
    #filename = secure_filename(file.filename) 
    # Check folder file
    if "/" in file.filename:
        filename = file.filename.split("/")[1]
    # Exclude over 2 word(".") rename filename
    split = filename.split(".")
    if len(split)>2:
        new_name = ""
        for idx, word in enumerate(split):
            if idx == 0:
                new_name = word
            elif idx < len(split)-1:
                new_name = new_name + "_" + word
            else:
                new_name = new_name + "." + word
        filename = new_name
    if is_import:
        filename_without_Extension=""
        for idx , name_piece in enumerate(filename.split(".")[0].split("_")):
            filename_without_Extension=filename_without_Extension+name_piece
            if idx==len(filename.split(".")[0].split("_"))-2:
                return filename , filename_without_Extension
            filename_without_Extension=filename_without_Extension+"_"
         
    return filename

def add_class_filename(class_key:str, filename:str):
    if class_key != "Unlabeled":
        filename = class_key + "_" + filename
    return filename

def same_name(dir_path:str, filename:str):
    # Split name
    orig_name = os.path.splitext(filename)
    # Added copy
    new_filename = orig_name[0] + "_copy" + orig_name[-1]
    # Same name
    if not "txt" in filename:
        # Find all *.* filename
        find_same_list = glob.glob( os.path.join(dir_path, '*' + orig_name[0] + '.*') )
        find_same_list = [path for path in find_same_list if not "txt" in path]
        find_same_list = [ path for path in find_same_list if orig_name[0] == os.path.splitext(os.path.split(path)[-1])[0] ]
        logging.warn("Same images:{}".format(find_same_list))
        # same name process
        new_filename = same_name(dir_path, new_filename) if len(find_same_list) > 0 else filename
    else:
        # TXT
        logging.warn("The file does exist:[{}/{}]".format(dir_path, filename))
        new_filename = same_name(dir_path, new_filename) if exists(os.path.join(dir_path, filename)) else filename
    return new_filename

def save_file(file, dir_path:str, filename:str):
    
    if filename != "classes.txt":
        if os.path.isfile(dir_path+filename):
            logging.warn("The file does exist:[{}/{}]".format(dir_path, filename))
            return True, filename
        filename = same_name(dir_path, filename)
        logging.warn("Change filename:[{}/{}]".format(dir_path, filename))
    # Same classes.txt problem
    if filename == "classes.txt":
        filename = "classes_temp.txt"
    # Save file
    file.save(os.path.join(dir_path, filename))
    logging.info('Upload file:[{}/{}]'.format(dir_path, filename))
    return True, filename

def compare_classes(dir_path:str, uuid:str):
    if exists(os.path.join(dir_path, "classes.txt")) and exists(os.path.join(dir_path, "classes_temp.txt")):
        class_text = get_classes_list(os.path.join(dir_path, "classes.txt"))
        class_temp_text = get_classes_list(os.path.join(dir_path, "classes_temp.txt"))
        if len(class_temp_text) >= len(class_text):
            os.remove(os.path.join(dir_path, "classes.txt"))
            os.rename(os.path.join(dir_path, "classes_temp.txt"), os.path.join(dir_path, "classes.txt"))
            # Update color id
            error_db = add_color_id_db_collector(class_temp_text, uuid, "workspace", del_key=True)
            if error_db:
                return error_db
        else:
            os.remove(os.path.join(dir_path, "classes_temp.txt"))

class Upload_DB():
    def __init__(self, uuid:str, prj_name:str, type:str, label:str, dir_path:str, filename:str):
        self.uuid = uuid
        self.label = label
        self.prj_name = prj_name
        self.dir_path = "".join(dir_path.split("workspace")[:-1]) + "workspace"
        self.filename = filename
        self.type = type
        self.folder = []
        self.classes_list = []

    # Fill in dictionary before database
    def upload_fillin_ws_info(self):
        # Check file exist
        if exists(self.dir_path + "/" + self.label + "/" + self.filename):
            # Check file type
            if self.filename.split(".")[-1] in ALLOWED_EXTENSIONS["label"]:
                error_db = self.label_action_db()
                # Prevent error 
                if error_db:
                    return error_db
            elif self.filename.split(".")[-1] in ALLOWED_EXTENSIONS["image"]:
                error_db = self.img_action_db()
                # Prevent error 
                if error_db:
                    return error_db
            # if self.type == "classification" and len(self.folder)>0:
            #     logging.info("Update class index in workspace of the database:[uuid:{}, type:classification]".format(self.uuid))
            #     thread_pool(self.cls_classes_db, self.folder)
            # Count wsdb for prjdb
            error_db = self.update_prj_db()
            # Prevent error 
            if error_db:
                return error_db
        else:
            msg = "The file does not exist:[{}]".format(self.filename)
            logging.error(str(msg))
            return ["error", msg]

    def check_classes_txt(self):  
        # Add a lock to prevent the sync calling function
        try:
            lock.acquire()  
            # Check classes.txt does exist
            classes_path = self.dir_path + "/classes.txt"
            if exists(classes_path):
                error_info = self.asymmetric_classe(classes_path)
                if error_info is not None:
                    return error_info
            else:
                # Create new classes.txt      
                error_info = create_classes(self.uuid, classes_path)
                if error_info is not None:
                    return error_info
                self.classes_list = get_classes_list(classes_path)
        except Exception as e:
            logging.error(str(e))
        finally:
            lock.release()

    def asymmetric_classe(self, classes_path:str):
        # Get classes length
        self.classes_list = get_classes_list(classes_path)
        if self.type == "object_detection":
            nums = self.obj_classes_txt()
            if len(self.classes_list) < nums:
                actual_list = list(range(len(self.classes_list), nums))
            else:
                logging.warn("The class length of classes.txt is equal to the class length of the database.")
                return
        elif self.type == "classification":
            nums = len(self.folder)
            if len(self.classes_list) < nums:
                actual_list = set(self.folder)^set(self.classes_list)
            else:
                logging.warn("The class length of classes.txt is equal to the class length of the database.")
                return
        # Reading color in color_table
        info_db = read_color_table_db()
        # Prevent error 
        if "error" in info_db:
            return info_db
        for idx, class_name in enumerate(actual_list):
            color_id = int(info_db[len(self.classes_list) + idx][0])
            # Append value in classes.txt
            add_class_txt(self.uuid, classes_path, str(class_name), int(color_id))
        # Update classes.txt
        self.classes_list = [cls for cls in read_txt(classes_path).split("\n") if cls !=""]
            
    def obj_classes_txt(self):
        # Get max value
        info_db = get_cls_max_db(self.uuid)
        # Prevent error 
        if "error" in info_db:
            return info_db
        if info_db[0][0] == None:
            info_db=[[-1]]
        return int(info_db[0][0])+1

    def check_img_db(self, txt:bool=False):
        if txt:
            split_name = os.path.splitext(self.filename)[0]
            # Collect all image format
            filename_list = [ "filename=\'{}\'".format(split_name + "." + fm) for fm in ALLOWED_EXTENSIONS["image"]]
            command =   """
                        SELECT filename FROM {} WHERE {};
                    """.format("workspace", "project_uuid=\'{}\' AND ({})".format(self.uuid, " OR ".join(filename_list)))
        else:
            value = "project_uuid=\'{}\' AND filename=\'{}\' AND img_path=\'{}/{}\'".format(self.uuid, self.filename, self.label, self.filename)
            command =   """
                            SELECT EXISTS (SELECT * FROM {} WHERE {});
                        """.format("workspace", value)
        info_db = execute_db(command, False)
        if "error" in info_db:
            return info_db
        return info_db

    def label_action_db(self):
        # Check classes.txt
        self.check_classes_txt()
        # Check img does exist in wsdb
        info_db = self.check_img_db(True)
        # Prevent error 
        if "error" in info_db:
            return info_db
        if len(info_db)>0:
            # Reading txt index
            txt_info = read_txt(self.dir_path + "/" + self.label + "/" + self.filename).split("\n")
            cls_idx = [int(row.split(" ")[0]) for row in txt_info if row != ""]
            # Save data in select img of wsdb
            error_db = update_data_table_cmd("workspace", 
                                                "annotate={}, cls_idx=\'{}\'".format(True, cls_idx), 
                                                "project_uuid=\'{}\' AND filename=\'{}\'".format(self.uuid, info_db[0][0]))
            if error_db:
                return error_db
            logging.info("Update data in the database:[uuid:{},filename:{}]".format(self.uuid, info_db[0][0]))

    def img_action_db(self):
        ws_info = copy.deepcopy(WS_INFO_DB)
        # Check type
        if self.type == "object_detection":
            # Save data to wsdict
            ws_info, _, _ = obj_fill_in_wsdict(self.uuid, 0, 0, self.dir_path, self.filename, ws_info)
        elif self.type == "classification":
            # path = "".join(self.dir_path.split("workspace")[:-1]) + "workspace"
            self.folder = [ f_name for f_name in natsorted(os.listdir(self.dir_path)) if os.path.isdir(self.dir_path+"/"+f_name)]
            # Create new classes.txt
            self.check_classes_txt()
            # Save data to wsdict
            if self.label in self.folder and self.label in self.classes_list:
                annotate = True
                idx = self.classes_list.index(self.label)
                dir = self.label
            else:
                annotate = False
                idx = None
                dir = ""
            ws_info, _, _ = cls_fill_in_wsdict(self.uuid, 0, 0, self.dir_path, dir, self.filename, ws_info, idx, annotate)
        # check is exist in database
        info_db = self.check_img_db()
        if "error" in info_db:
            return info_db
        # Save data to database
        if not(info_db[0][0]):
            error_db = fill_in_db(ws_info, 0, "workspace")
            if error_db:
                return error_db
            logging.info("Added data in the database:[uuid:{},filename:{}]".format(self.uuid, self.filename))

    def update_prj_db(self):
        # Check anntation
        command =   """
                        SELECT {} FROM {} WHERE {};
                    """.format("annotate, img_path",  "workspace", "project_uuid=\'{}\'".format(self.uuid))
        # Exclude status when data exists in DB
        info_db = execute_db(command, False)
        # Prevent error 
        if "error" in info_db:
            return info_db
        # Collect numbers
        false_num = len([ value[0] for value in info_db if value[0] == False])
        true_num = len([ value[0] for value in info_db if value[0] == True])
        img_path = ""
        if info_db == []:
            main_path = "{}/{}".format(ROOT, self.prj_name)
            cover_path = [ os.path.join(main_path, name) for name in os.listdir(main_path) if os.path.isfile(os.path.join(main_path, name)) ]
            if len(cover_path) > 0:
                os.remove(cover_path[0])
            img_path = ""
        else:
            if info_db[0][1] != None:
                # Create cover image
                img_path = "{}/{}/workspace/{}".format(ROOT, self.prj_name, info_db[0][1])
                save_path = "{}/{}/cover.{}".format(ROOT, self.prj_name, info_db[0][1].split(".")[-1])
                if not exists(save_path):
                    shutil.copyfile(img_path, save_path)
                img_path = "/display_img/project/{}/cover.{}".format(self.prj_name, info_db[0][1].split(".")[-1])

        # Update project
        values = "effect_img_nums={},unlabeled_img_nums={},show_image_path=\'{}\'".format(true_num, false_num, img_path)
        select = "project_uuid=\'{}\'".format(self.uuid)
        error_db = update_data_table_cmd("project", values, select)
        if error_db:
            return error_db
        logging.info("Update data in project of the the database:[uuid:{}]".format(self.uuid))

    # def cls_classes_db(self, label:str):
    #     idx = self.folder.index(label)
    #     values = "cls_idx=\'{}\'".format([idx])
    #     select = "project_uuid=\'{}\' AND img_path LIKE \'%\' || \'{}/\' || \'%\';".format(self.uuid, label)
    #     error_db = update_data_table_cmd('workspace', values, select)
    #     if error_db:
    #         return error_db