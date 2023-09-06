import os
import sys
import shutil
from argparse import ArgumentParser, SUPPRESS

# Silence TensorFlow messages
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

import tensorflow as tf
from tensorflow.keras import backend as K
from tensorflow.keras.models import load_model

##################################################################################
def build_argparser():
    parser = ArgumentParser(add_help=False)
    args = parser.add_argument_group('Options')
    args.add_argument('-h', '--help', action='help', default=SUPPRESS, help='Show this help message and exit.')
    args.add_argument('-m', '--model', required=True, help = "The path of converting model")
    args.add_argument('-o', '--output', required=True, help = "The save path of converted model")
    return parser


def main(args):
    # set learning phase for no training: This line must be executed before loading Keras model
    K.set_learning_phase(0)

    path = os.path.split(args.model)
    model_name = os.path.splitext(path[-1])[0]
    model = load_model(args.model)
    # # make list of output node names
    # output_names = [out.op.name for out in model.outputs]

    # set up tensorflow saver object
    saver = tf.compat.v1.train.Saver()

    # fetch the tensorflow session using the Keras backend
    sess = tf.compat.v1.keras.backend.get_session()

    # Check the input and output name
    print ("\n TF input node name:")
    print(model.inputs)
    print ("\n TF output node name:")
    print(model.outputs)

    # write out tensorflow checkpoint & meta graph
    # saver.save(sess, os.path.join(path[0], model_name + ".ckpt"))
    saver.save(sess, args.output)
    print ("\nFINISHED CREATING TF FILES\n")
    
if __name__ == '__main__':
    args = build_argparser().parse_args()
    sys.exit(main(args) or 0)
