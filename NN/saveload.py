# -*- coding: utf-8 -*-
"""saveload.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1_3TwlXivwccRp0XfBoCdkw5rv_TkXWCF
"""

import torch
import torchvision.models as models

model = models.vgg16(weights='IMAGENET1K_V1')
torch.save(model.state_dict(), 'model_weights.pth')

model = models.vgg16()
model.load_state_dict(torch.load('model_weights.pth'))
model.eval()

torch.save(model, 'model.pth')

model = torch.load('model.pth')