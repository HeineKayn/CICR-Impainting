import torch.nn as nn

class SubPixelNetwork(nn.Module):
    def __init__(self, upscale_factor):
        super(SubPixelNetwork, self).__init__()

        self.relu = nn.ReLU()
        self.conv1 = nn.Conv2d(3, 64, (5, 5), (1, 1), (2, 2))
        self.conv2 = nn.Conv2d(64, 64, (3, 3), (1, 1), (1, 1))
        self.conv3 = nn.Conv2d(64, 32, (3, 3), (1, 1), (1, 1))
        self.conv4 = nn.Conv2d(32, (upscale_factor ** 2)*3, (3, 3), (1, 1), (1, 1))
        
        # Sub-pixel convolution: rearranges elements in a Tensor of shape (*, r^2C, H, W)
        # to a tensor of shape (C, rH, rW)
        self.pixel_shuffle = nn.PixelShuffle(upscale_factor)


    def forward(self, x):
        x = self.relu(self.conv1(x))
        x = self.relu(self.conv2(x))
        x = self.relu(self.conv3(x))
        x = self.pixel_shuffle(self.conv4(x))
        return x