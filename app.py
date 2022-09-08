from common.logger import config_logger
import argparse

from webapi import app, socketio
from webapi.control_project import app_cl_pj
from webapi.upload_dataset import app_ud_dt
from webapi.display_dataset import app_dy_dt
from webapi.labeling import app_labeling
from webapi.augmentation import app_aug
from webapi.control_model import app_cl_model
from webapi.train_model import app_train
from webapi.export_model import app_export
from webapi.evaluate_model import app_eval

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-port", "--port", help="Input port number")
    args = parser.parse_args()
    
    app.register_blueprint(app_cl_pj)
    app.register_blueprint(app_ud_dt)
    app.register_blueprint(app_dy_dt)
    app.register_blueprint(app_aug)
    app.register_blueprint(app_labeling)
    app.register_blueprint(app_cl_model)
    app.register_blueprint(app_train)
    app.register_blueprint(app_export)
    app.register_blueprint(app_eval)

    config_logger('./app.log', 'w', "info")
    socketio.run(app, host = "0.0.0.0", port=args.port, debug=False)