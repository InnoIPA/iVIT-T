import logging, sys
from argparse import ArgumentParser, SUPPRESS
from webapi import app, socketio
from webapi.control_project import app_cl_pj
from webapi.upload_dataset import app_ud_dt
from webapi.display_dataset import app_dy_dt
from webapi.labeling import app_labeling
from webapi.augmentation import app_aug
from webapi.control_model import app_cl_model
from webapi.training_model import app_train
from webapi.export_model import app_export
from webapi.evaluate_model import app_eval
from webapi.icap import app_icap
from webapi.common.database import init_db
from webapi.common.init_tool import init_sample_to_db
from webapi.common.thingsboard import init_for_icap
import webapi.common.config
from common.logger import config_logger

def build_argparser():
    parser = ArgumentParser(add_help=False)
    args = parser.add_argument_group('Options')
    args.add_argument('-h', '--help', action='help', default=SUPPRESS, help='Show this help message and exit.')
    args.add_argument('-port', '--port', required=True, help = "Input port number")
    return parser

def main(args):
    # Create initial table in db
    logging.info("Initial database...")
    init_db()
    # Fill in db from sample
    logging.info("Initial sample project...")
    init_sample_to_db()

    app.register_blueprint(app_cl_pj)
    app.register_blueprint(app_ud_dt)
    app.register_blueprint(app_dy_dt)
    app.register_blueprint(app_aug)
    app.register_blueprint(app_labeling)
    app.register_blueprint(app_cl_model)
    app.register_blueprint(app_train)
    app.register_blueprint(app_export)
    app.register_blueprint(app_eval)
    app.register_blueprint(app_icap)

    # Register iCAP
    logging.info("Initial iCAP register...")
    init_for_icap()
    # Running webapi sever
    logging.info("Running webapi server...")
    socketio.run(app, host = "0.0.0.0", port=args.port, debug=False)

if __name__ == '__main__':
    # Create log
    config_logger('./app.log', 'w', "info")
    args = build_argparser().parse_args()
    sys.exit(main(args) or 0)