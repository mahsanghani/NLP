# -*- coding: utf-8 -*-
"""Tutorial_2_train_your_first_TTS_model

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/18OUIj2PFXYVY0TG3pVfqwsQ4Bul0QRIb

# Train your first 🐸 TTS model 💫

### 👋 Hello and welcome to Coqui (🐸) TTS

The goal of this notebook is to show you a **typical workflow** for **training** and **testing** a TTS model with 🐸.

Let's train a very small model on a very small amount of data so we can iterate quickly.

In this notebook, we will:

1. Download data and format it for 🐸 TTS.
2. Configure the training and testing runs.
3. Train a new model.
4. Test the model and display its performance.

So, let's jump right in!
"""

## Install Coqui TTS
! pip install -U pip
! pip install TTS

"""## ✅ Data Preparation

### **First things first**: we need some data.

We're training a Text-to-Speech model, so we need some _text_ and we need some _speech_. Specificially, we want _transcribed speech_. The speech must be divided into audio clips and each clip needs transcription. More details about data requirements such as recording characteristics, background noise and vocabulary coverage can be found in the [🐸TTS documentation](https://tts.readthedocs.io/en/latest/formatting_your_dataset.html).

If you have a single audio file and you need to **split** it into clips. It is also important to use a lossless audio file format to prevent compression artifacts. We recommend using **wav** file format.

The data format we will be adopting for this tutorial is taken from the widely-used  **LJSpeech** dataset, where **waves** are collected under a folder:

<span style="color:purple;font-size:15px">
/wavs<br />
 &emsp;| - audio1.wav<br />
 &emsp;| - audio2.wav<br />
 &emsp;| - audio3.wav<br />
  ...<br />
</span>

and a **metadata.csv** file will have the audio file name in parallel to the transcript, delimited by `|`:

<span style="color:purple;font-size:15px">
# metadata.csv <br />
audio1|This is my sentence. <br />
audio2|This is maybe my sentence. <br />
audio3|This is certainly my sentence. <br />
audio4|Let this be your sentence. <br />
...
</span>

In the end, we should have the following **folder structure**:

<span style="color:purple;font-size:15px">
/MyTTSDataset <br />
&emsp;| <br />
&emsp;| -> metadata.csv<br />
&emsp;| -> /wavs<br />
&emsp;&emsp;| -> audio1.wav<br />
&emsp;&emsp;| -> audio2.wav<br />
&emsp;&emsp;| ...<br />
</span>

🐸TTS already provides tooling for the _LJSpeech_. if you use the same format, you can start training your models right away. <br />

After you collect and format your dataset, you need to check two things. Whether you need a **_formatter_** and a **_text_cleaner_**. <br /> The **_formatter_** loads the text file (created above) as a list and the **_text_cleaner_** performs a sequence of text normalization operations that converts the raw text into the spoken representation (e.g. converting numbers to text, acronyms, and symbols to the spoken format).

If you use a different dataset format then the LJSpeech or the other public datasets that 🐸TTS supports, then you need to write your own **_formatter_** and  **_text_cleaner_**.

## ⏳️ Loading your dataset
Load one of the dataset supported by 🐸TTS.

We will start by defining dataset config and setting LJSpeech as our target dataset and define its path.
"""

import os

# BaseDatasetConfig: defines name, formatter and path of the dataset.
from TTS.tts.configs.shared_configs import BaseDatasetConfig

output_path = "tts_train_dir"
if not os.path.exists(output_path):
    os.makedirs(output_path)

# Download and extract LJSpeech dataset.

!wget -O $output_path/LJSpeech-1.1.tar.bz2 https://data.keithito.com/data/speech/LJSpeech-1.1.tar.bz2
!tar -xf $output_path/LJSpeech-1.1.tar.bz2 -C $output_path

dataset_config = BaseDatasetConfig(
    formatter="ljspeech", meta_file_train="metadata.csv", path=os.path.join(output_path, "LJSpeech-1.1/")
)

"""## ✅ Train a new model

Let's kick off a training run 🚀🚀🚀.

Deciding on the model architecture you'd want to use is based on your needs and available resources. Each model architecture has it's pros and cons that define the run-time efficiency and the voice quality.
We have many recipes under `TTS/recipes/` that provide a good starting point. For this tutorial, we will be using `GlowTTS`.

We will begin by initializing the model training configuration.
"""

# GlowTTSConfig: all model related values for training, validating and testing.
from TTS.tts.configs.glow_tts_config import GlowTTSConfig
config = GlowTTSConfig(
    batch_size=32,
    eval_batch_size=16,
    num_loader_workers=4,
    num_eval_loader_workers=4,
    run_eval=True,
    test_delay_epochs=-1,
    epochs=100,
    text_cleaner="phoneme_cleaners",
    use_phonemes=True,
    phoneme_language="en-us",
    phoneme_cache_path=os.path.join(output_path, "phoneme_cache"),
    print_step=25,
    print_eval=False,
    mixed_precision=True,
    output_path=output_path,
    datasets=[dataset_config],
    save_step=1000,
)

"""Next we will initialize the audio processor which is used for feature extraction and audio I/O."""

from TTS.utils.audio import AudioProcessor
ap = AudioProcessor.init_from_config(config)
# Modify sample rate if for a custom audio dataset:
# ap.sample_rate = 22050

"""Next we will initialize the tokenizer which is used to convert text to sequences of token IDs.  If characters are not defined in the config, default characters are passed to the config."""

from TTS.tts.utils.text.tokenizer import TTSTokenizer
tokenizer, config = TTSTokenizer.init_from_config(config)

"""Next we will load data samples. Each sample is a list of ```[text, audio_file_path, speaker_name]```. You can define your custom sample loader returning the list of samples."""

from TTS.tts.datasets import load_tts_samples
train_samples, eval_samples = load_tts_samples(
    dataset_config,
    eval_split=True,
    eval_split_max_size=config.eval_split_max_size,
    eval_split_size=config.eval_split_size,
)

"""Now we're ready to initialize the model.

Models take a config object and a speaker manager as input. Config defines the details of the model like the number of layers, the size of the embedding, etc. Speaker manager is used by multi-speaker models.
"""

from TTS.tts.models.glow_tts import GlowTTS
model = GlowTTS(config, ap, tokenizer, speaker_manager=None)

"""Trainer provides a generic API to train all the 🐸TTS models with all its perks like mixed-precision training, distributed training, etc."""

from trainer import Trainer, TrainerArgs
trainer = Trainer(
    TrainerArgs(), config, output_path, model=model, train_samples=train_samples, eval_samples=eval_samples
)

"""### AND... 3,2,1... START TRAINING 🚀🚀🚀"""

trainer.fit()

"""#### 🚀 Run the Tensorboard. 🚀
On the notebook and Tensorboard, you can monitor the progress of your model. Also Tensorboard provides certain figures and sample outputs.
"""

!pip install tensorboard
!tensorboard --logdir=tts_train_dir

"""## ✅ Test the model

We made it! 🙌

Let's kick off the testing run, which displays performance metrics.

We're committing the cardinal sin of ML 😈 (aka - testing on our training data) so you don't want to deploy this model into production. In this notebook we're focusing on the workflow itself, so it's forgivable 😇

You can see from the test output that our tiny model has overfit to the data, and basically memorized this one sentence.

When you start training your own models, make sure your testing data doesn't include your training data 😅

Let's get the latest saved checkpoint.
"""

import glob, os
output_path = "tts_train_dir"
ckpts = sorted([f for f in glob.glob(output_path+"/*/*.pth")])
configs = sorted([f for f in glob.glob(output_path+"/*/*.json")])

!tts --text "Text for TTS" \
      --model_path $test_ckpt \
      --config_path $test_config \
      --out_path out.wav

"""## 📣 Listen to the synthesized wave 📣"""

import IPython
IPython.display.Audio("out.wav")

"""## 🎉 Congratulations! 🎉 You now have trained your first TTS model!
Follow up with the next tutorials to learn more advanced material.
"""
