# -*- coding: utf-8 -*-
"""emo.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1vD97CnAgSH5xoAXCako2OiAxxQsk4GY5
"""

!pip install speechbrain
!pip install transformer

from speechbrain.pretrained.interfaces import foreign_class
classifier = foreign_class(source="speechbrain/emotion-recognition-wav2vec2-IEMOCAP", pymodule_file="custom_interface.py", classname="CustomEncoderWav2vec2Classifier")
out_prob, score, index, text_lab = classifier.classify_file("anger.wav")
print(out_prob)
print(score)
print(index)
print(text_lab)


