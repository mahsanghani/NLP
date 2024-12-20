# -*- coding: utf-8 -*-
"""load_checkpoints.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1t-jXIsMmDBiGfpk1na5BKbuxyc309lPx
"""

!pip install -U -q "tf-models-official"

import os
import yaml
import json

import tensorflow as tf
import tensorflow_models as tfm

from official.core import exp_factory

# @title Download Checkpoint of the Selected Model { display-mode: "form", run: "auto" }
model_display_name = 'BERT-base uncased English'  # @param ['BERT-base uncased English','BERT-base cased English','BERT-large uncased English', 'BERT-large cased English', 'BERT-large, Uncased (Whole Word Masking)', 'BERT-large, Cased (Whole Word Masking)', 'BERT-base MultiLingual','BERT-base Chinese']

if model_display_name == 'BERT-base uncased English':
  !wget "https://storage.googleapis.com/tf_model_garden/nlp/bert/v3/uncased_L-12_H-768_A-12.tar.gz"
  !tar -xvf "uncased_L-12_H-768_A-12.tar.gz"
elif model_display_name == 'BERT-base cased English':
  !wget "https://storage.googleapis.com/tf_model_garden/nlp/bert/v3/cased_L-12_H-768_A-12.tar.gz"
  !tar -xvf "cased_L-12_H-768_A-12.tar.gz"
elif model_display_name == "BERT-large uncased English":
  !wget "https://storage.googleapis.com/tf_model_garden/nlp/bert/v3/uncased_L-24_H-1024_A-16.tar.gz"
  !tar -xvf "uncased_L-24_H-1024_A-16.tar.gz"
elif model_display_name == "BERT-large cased English":
  !wget "https://storage.googleapis.com/tf_model_garden/nlp/bert/v3/cased_L-24_H-1024_A-16.tar.gz"
  !tar -xvf "cased_L-24_H-1024_A-16.tar.gz"
elif model_display_name == "BERT-large, Uncased (Whole Word Masking)":
  !wget "https://storage.googleapis.com/tf_model_garden/nlp/bert/v3/wwm_uncased_L-24_H-1024_A-16.tar.gz"
  !tar -xvf "wwm_uncased_L-24_H-1024_A-16.tar.gz"
elif model_display_name == "BERT-large, Cased (Whole Word Masking)":
  !wget "https://storage.googleapis.com/tf_model_garden/nlp/bert/v3/wwm_cased_L-24_H-1024_A-16.tar.gz"
  !tar -xvf "wwm_cased_L-24_H-1024_A-16.tar.gz"
elif model_display_name == "BERT-base MultiLingual":
  !wget "https://storage.googleapis.com/tf_model_garden/nlp/bert/v3/multi_cased_L-12_H-768_A-12.tar.gz"
  !tar -xvf "multi_cased_L-12_H-768_A-12.tar.gz"
elif model_display_name == "BERT-base Chinese":
  !wget "https://storage.googleapis.com/tf_model_garden/nlp/bert/v3/chinese_L-12_H-768_A-12.tar.gz"
  !tar -xvf "chinese_L-12_H-768_A-12.tar.gz"

# Lookup table of the directory name corresponding to each model checkpoint
folder_bert_dict = {
    'BERT-base uncased English': 'uncased_L-12_H-768_A-12',
    'BERT-base cased English': 'cased_L-12_H-768_A-12',
    'BERT-large uncased English': 'uncased_L-24_H-1024_A-16',
    'BERT-large cased English': 'cased_L-24_H-1024_A-16',
    'BERT-large, Uncased (Whole Word Masking)': 'wwm_uncased_L-24_H-1024_A-16',
    'BERT-large, Cased (Whole Word Masking)': 'wwm_cased_L-24_H-1024_A-16',
    'BERT-base MultiLingual': 'multi_cased_L-12_H-768_A-1',
    'BERT-base Chinese': 'chinese_L-12_H-768_A-12'
}

folder_bert = folder_bert_dict.get(model_display_name)
folder_bert

config_file = os.path.join(folder_bert, "params.yaml")
config_dict = yaml.safe_load(tf.io.gfile.GFile(config_file).read())
config_dict

# Method 1: pass encoder config dict into EncoderConfig
encoder_config = tfm.nlp.encoders.EncoderConfig(config_dict["task"]["model"]["encoder"])
encoder_config.get().as_dict()

# Method 2: use override_params_dict function to override default Encoder params
encoder_config = tfm.nlp.encoders.EncoderConfig()
tfm.hyperparams.override_params_dict(encoder_config, config_dict["task"]["model"]["encoder"], is_strict=True)
encoder_config.get().as_dict()

bert_config_file = os.path.join(folder_bert, "bert_config.json")
config_dict = json.loads(tf.io.gfile.GFile(bert_config_file).read())
config_dict

encoder_config = tfm.nlp.encoders.EncoderConfig({
    'type':'bert',
    'bert': config_dict
})

encoder_config.get().as_dict()

bert_encoder = tfm.nlp.encoders.build_encoder(encoder_config)
bert_classifier = tfm.nlp.models.BertClassifier(network=bert_encoder, num_classes=2)

tf.keras.utils.plot_model(bert_classifier)

checkpoint = tf.train.Checkpoint(encoder=bert_encoder)
checkpoint.read(
    os.path.join(folder_bert, 'bert_model.ckpt')).expect_partial().assert_existing_objects_matched()

# @title Download Checkpoint of the Selected Model { display-mode: "form", run: "auto" }
albert_model_display_name = 'ALBERT-base English'  # @param ['ALBERT-base English', 'ALBERT-large English', 'ALBERT-xlarge English', 'ALBERT-xxlarge English']

if albert_model_display_name == 'ALBERT-base English':
  !wget "https://storage.googleapis.com/tf_model_garden/nlp/albert/albert_base.tar.gz"
  !tar -xvf "albert_base.tar.gz"
elif albert_model_display_name == 'ALBERT-large English':
  !wget "https://storage.googleapis.com/tf_model_garden/nlp/albert/albert_large.tar.gz"
  !tar -xvf "albert_large.tar.gz"
elif albert_model_display_name == "ALBERT-xlarge English":
  !wget "https://storage.googleapis.com/tf_model_garden/nlp/albert/albert_xlarge.tar.gz"
  !tar -xvf "albert_xlarge.tar.gz"
elif albert_model_display_name == "ALBERT-xxlarge English":
  !wget "https://storage.googleapis.com/tf_model_garden/nlp/albert/albert_xxlarge.tar.gz"
  !tar -xvf "albert_xxlarge.tar.gz"

# Lookup table of the directory name corresponding to each model checkpoint
folder_albert_dict = {
    'ALBERT-base English': 'albert_base',
    'ALBERT-large English': 'albert_large',
    'ALBERT-xlarge English': 'albert_xlarge',
    'ALBERT-xxlarge English': 'albert_xxlarge'
}

folder_albert = folder_albert_dict.get(albert_model_display_name)
folder_albert

config_file = os.path.join(folder_albert, "params.yaml")
config_dict = yaml.safe_load(tf.io.gfile.GFile(config_file).read())
config_dict

# Method 1: pass encoder config dict into EncoderConfig
encoder_config = tfm.nlp.encoders.EncoderConfig(config_dict["task"]["model"]["encoder"])
encoder_config.get().as_dict()

# Method 2: use override_params_dict function to override default Encoder params
encoder_config = tfm.nlp.encoders.EncoderConfig()
tfm.hyperparams.override_params_dict(encoder_config, config_dict["task"]["model"]["encoder"], is_strict=True)
encoder_config.get().as_dict()

albert_config_file = os.path.join(folder_albert, "albert_config.json")
config_dict = json.loads(tf.io.gfile.GFile(albert_config_file).read())
config_dict

encoder_config = tfm.nlp.encoders.EncoderConfig({
    'type':'albert',
    'albert': config_dict
})

encoder_config.get().as_dict()

albert_encoder = tfm.nlp.encoders.build_encoder(encoder_config)
albert_classifier = tfm.nlp.models.BertClassifier(network=albert_encoder, num_classes=2)

tf.keras.utils.plot_model(albert_classifier)

checkpoint = tf.train.Checkpoint(encoder=albert_encoder)
checkpoint.read(
    os.path.join(folder_albert, 'bert_model.ckpt')).expect_partial().assert_existing_objects_matched()

# @title Download Checkpoint of the Selected Model { display-mode: "form", run: "auto" }
electra_model_display_name = 'ELECTRA-small English'  # @param ['ELECTRA-small English', 'ELECTRA-base English']

if electra_model_display_name == 'ELECTRA-small English':
  !wget "https://storage.googleapis.com/tf_model_garden/nlp/electra/small.tar.gz"
  !tar -xvf "small.tar.gz"
elif electra_model_display_name == 'ELECTRA-base English':
  !wget "https://storage.googleapis.com/tf_model_garden/nlp/electra/base.tar.gz"
  !tar -xvf "base.tar.gz"

# Lookup table of the directory name corresponding to each model checkpoint
folder_electra_dict = {
    'ELECTRA-small English': 'small',
    'ELECTRA-base English': 'base'
}

folder_electra = folder_electra_dict.get(electra_model_display_name)
folder_electra

config_file = os.path.join(folder_electra, "params.yaml")
config_dict = yaml.safe_load(tf.io.gfile.GFile(config_file).read())
config_dict

disc_encoder_config = tfm.nlp.encoders.EncoderConfig(
    config_dict['model']['discriminator_encoder']
)

disc_encoder_config.get().as_dict()

disc_encoder = tfm.nlp.encoders.build_encoder(disc_encoder_config)
elctra_dic_classifier = tfm.nlp.models.BertClassifier(network=disc_encoder, num_classes=2)
tf.keras.utils.plot_model(elctra_dic_classifier)

checkpoint = tf.train.Checkpoint(encoder=disc_encoder)
checkpoint.read(
    tf.train.latest_checkpoint(os.path.join(folder_electra))
    ).expect_partial().assert_existing_objects_matched()

