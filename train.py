from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os
import json

import tensorflow as tf

from qa_model import Encoder, QASystem, Decoder
from os.path import join as pjoin
import numpy as np

from utils.read_data import mask_dataset
from utils.read_data import read_answers, read_raw_answers
from Config import Config as cfg
import time

import logging

logging.basicConfig(level=logging.INFO)

tf.app.flags.DEFINE_string("load_train_dir", "", "Training directory to load model parameters from to resume training (default: {train_dir}).")

FLAGS = tf.app.flags.FLAGS


def initialize_model(session, model, train_dir):
    ckpt = tf.train.get_checkpoint_state(train_dir)
    v2_path = ckpt.model_checkpoint_path + ".index" if ckpt else ""
    if ckpt and (tf.gfile.Exists(ckpt.model_checkpoint_path) or tf.gfile.Exists(v2_path)):
        logging.info("Reading model parameters from %s" % ckpt.model_checkpoint_path)
        model.saver.restore(session, ckpt.model_checkpoint_path)
    else:
        logging.info("Created model with fresh parameters.")
        session.run(tf.global_variables_initializer())
        logging.info('Num params: %d' % sum(v.get_shape().num_elements() for v in tf.trainable_variables()))
    return model


def initialize_vocab(vocab_path):
    if tf.gfile.Exists(vocab_path):
        rev_vocab = []
        with tf.gfile.GFile(vocab_path, mode="rb") as f:
            rev_vocab.extend(f.readlines())
        rev_vocab = [line.strip('\n') for line in rev_vocab]
        # (word, index)
        vocab = dict([(x, y) for (y, x) in enumerate(rev_vocab)])
        return vocab, rev_vocab
    else:
        raise ValueError("Vocabulary file %s not found.", vocab_path)


def get_normalized_train_dir(train_dir):
    """
    Adds symlink to {train_dir} from /tmp/cs224n-squad-train to canonicalize the
    file paths saved in the checkpoint. This allows the model to be reloaded even
    if the location of the checkpoint files has moved, allowing usage with CodaLab.
    This must be done on both train.py and qa_answer.py in order to work.
    """
    global_train_dir = '/tmp/cs224n-squad-train'
    if os.path.exists(global_train_dir):
        os.unlink(global_train_dir)
    if not os.path.exists(train_dir):
        os.makedirs(train_dir)
    os.symlink(os.path.abspath(train_dir), global_train_dir)
    return global_train_dir


def main(_):

    data_dir = cfg.DATA_DIR
    set_names = cfg.set_names
    suffixes = cfg.suffixes
    dataset = mask_dataset(data_dir, set_names, suffixes)
    answers = read_answers(data_dir)
    raw_answers = read_raw_answers(data_dir)

    vocab_path = pjoin(data_dir, cfg.vocab_file)
    vocab, rev_vocab = initialize_vocab(vocab_path)

    c_time = time.strftime('%Y%m%d_%H%M',time.localtime())
    if not os.path.exists(cfg.log_dir):
        os.makedirs(cfg.log_dir)
    if not os.path.exists(cfg.cache_dir):
        os.makedirs(cfg.cache_dir)
    if not os.path.exists(cfg.fig_dir):
        os.makedirs(cfg.fig_dir)
    file_handler = logging.FileHandler(pjoin(cfg.log_dir, 'log'+c_time+'.txt'))
    logging.getLogger().addHandler(file_handler)

    print(vars(FLAGS))
    with open(os.path.join(cfg.log_dir, "flags.json"), 'w') as fout:
        json.dump(FLAGS.__flags, fout)

    #gpu setting
    config = tf.ConfigProto()
    config.gpu_options.allow_growth = True

    tf.reset_default_graph()

    encoder = Encoder(size=2*cfg.lstm_num_hidden)
    decoder = Decoder(output_size=2*cfg.lstm_num_hidden)
    qa = QASystem(encoder, decoder)

    with tf.Session(config=config) as sess:
        init = tf.global_variables_initializer()
        sess.run(init)
        load_train_dir = get_normalized_train_dir(cfg.train_dir)
        logging.info('=========== trainable varaibles ============')
        for i in tf.trainable_variables():
            logging.info(i.name)
        logging.info('=========== regularized varaibles ============')
        for i in tf.get_collection(tf.GraphKeys.REGULARIZATION_LOSSES):
            logging.info(i.name)

        initialize_model(sess, qa, load_train_dir)

        save_train_dir = get_normalized_train_dir(cfg.train_dir)
        qa.train(cfg.start_lr, sess,dataset,answers,save_train_dir, raw_answers=raw_answers,
        #          debug_num=100,
                 rev_vocab=rev_vocab)
        qa.evaluate_answer(sess, dataset, raw_answers, rev_vocab,
             log=True,
             training=False,
             sample=4000)

if __name__ == "__main__":
    tf.app.run()
