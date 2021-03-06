from matplotlib.pyplot import install_repl_displayhook
import torch.nn as nn
from torch.nn.modules.activation import LeakyReLU
from torch.nn.modules.batchnorm import BatchNorm1d, BatchNorm2d
from torch.nn.modules.conv import Conv2d
import torch.optim as optim


class Generator(nn.Module):
    """ Generator part of DCGAN model """
    def __init__(self, latent_vector_size, feature_map, num_channels, conditional=False):
        super(Generator, self).__init__()
        self.latent_vector = latent_vector_size
        self.feature_map = feature_map
        self.channels = num_channels
        self.criterion = None
        self.optimizer = None
        self.main = None
        self.conditional = conditional

    def build(self):
        """ Builds model with Sequential definition """
        if self.conditional:
            """ Context Encoder Network """
            self.main = nn.Sequential(   
                # Encoder         
                # Input is image: channels x 64 x 64
                nn.Conv2d(self.channels, self.feature_map, 4, 2, 1),
                nn.LeakyReLU(0.2, inplace=True),
                # State size: feature_map x 32 x 32
                nn.Conv2d(self.feature_map, self.feature_map, 4, 2, 1),
                nn.BatchNorm2d(self.feature_map),
                nn.LeakyReLU(0.2, inplace=True),
                # State size: feature_map x 16 x 16
                nn.Conv2d(self.feature_map, self.feature_map * 2, 4, 2, 1),
                nn.BatchNorm2d(self.feature_map * 2),
                nn.LeakyReLU(0.2, inplace=True),
                # State size: (feature_map * 2) x 8 x 8
                nn.Conv2d(self.feature_map * 2, self.feature_map * 4, 4, 2, 1),
                nn.BatchNorm2d(self.feature_map * 4),
                nn.LeakyReLU(0.2, inplace=True),
                # State size: (feature_map * 4) x 4 x 4
                nn.Conv2d(self.feature_map * 4, self.feature_map * 8, 4, 2, 1),
                nn.BatchNorm2d(self.feature_map * 8),
                nn.LeakyReLU(0.2, inplace=True),

                # Bottleneck
                nn.Conv2d(self.feature_map * 8, 4000, 4),
                nn.BatchNorm2d(4000),
                nn.ReLU(),

                # Decoder
                # State size: (feature_map * 8) x 4 x 4
                nn.ConvTranspose2d(self.feature_map * 8, self.feature_map * 4, 4, 2, 1),
                nn.BatchNorm2d(self.feature_map * 4),
                nn.ReLU(),
                # State size: (feature_map * 4) x 8 x 8
                nn.ConvTranspose2d(self.feature_map * 4, self.feature_map * 2, 4, 2, 1),
                nn.BatchNorm2d(self.feature_map * 2),
                nn.ReLU(),
                # State size: (feature_map * 2) x 16 x 16
                nn.ConvTranspose2d(self.feature_map * 2, self.feature_map, 4, 2, 1),
                nn.BatchNorm2d(self.feature_map),
                nn.ReLU(),
                # State size: (feature_map) x 32 x 32
                nn.ConvTranspose2d(self.feature_map, self.channels, 4, 2, 1),
                nn.Tanh()
                # Output size: channels x 64 x 64
            )
        else:
            """ DCGAN Network """
            self.main = nn.Sequential(
                # Input is latent vector
                nn.ConvTranspose2d(self.latent_vector, self.feature_map * 8, 4, 1, 0, bias=False),
                nn.BatchNorm2d(self.feature_map * 8),
                nn.ReLU(True),
                # state size: (feature_map*8) x 4 x 4
                nn.ConvTranspose2d(self.feature_map * 8, self.feature_map * 4, 4, 2, 1, bias=False),
                nn.BatchNorm2d(self.feature_map * 4),
                nn.ReLU(True),
                # state size: (feature_map*4) x 8 x 8
                nn.ConvTranspose2d(self.feature_map * 4, self.feature_map * 2, 4, 2, 1, bias=False),
                nn.BatchNorm2d(self.feature_map * 2),
                nn.ReLU(True),
                # state size: (feature_map*2) x 16 x 16
                nn.ConvTranspose2d(self.feature_map * 2, self.feature_map, 4, 2, 1, bias=False),
                nn.BatchNorm2d(self.feature_map),
                nn.ReLU(True),
                # state size: (feature_map) x 32 x 32
                nn.ConvTranspose2d(self.feature_map, self.channels, 4, 2, 1, bias=False),
                nn.Tanh()
                # Output is image: channels x 64 x 64
            )


    def forward(self, input):
        """ Perform forward pass """
        return self.main(input)

    def define_optim(self, learning_rate, beta1):
        self.optimizer = optim.Adam(self.main.parameters(), lr=learning_rate, betas=(beta1, 0.999))

    @staticmethod
    def init_weights(layers):
        """ Randomly initialize weights from Normal distribution with mean = 0, std = 0.02 """
        classname = layers.__class__.__name__
        if classname.find('Conv') != -1:
            nn.init.normal_(layers.weight.data, 0.0, 0.02)
        elif classname.find('BatchNorm') != -1:
            nn.init.normal_(layers.weight.data, 1.0, 0.02)
            nn.init.constant_(layers.bias.data, 0)


class Discriminator(nn.Module):
    """ Discriminator part of DCGAN model """
    def __init__(self, latent_vector_size, feature_map, num_channels, conditional=False):
        super(Discriminator, self).__init__()
        self.latent_vector = latent_vector_size
        self.feature_map = feature_map
        self.channels = num_channels
        self.criterion = None
        self.optimizer = None
        self.main = None
        self.conditional = conditional

    def build(self):
        """ Builds model with Sequential definition """
        bias = True if self.conditional else False
        self.main = nn.Sequential(
            # Input is image: channels x 64 x 64
            nn.Conv2d(self.channels, self.feature_map, 4, 2, 1, bias=bias),
            nn.LeakyReLU(0.2, inplace=True),
            # State size: (feature_map) x 32 x 32
            nn.Conv2d(self.feature_map, self.feature_map * 2, 4, 2, 1, bias=bias),
            nn.BatchNorm2d(self.feature_map * 2),
            nn.LeakyReLU(0.2, inplace=True),
            # State size: (feature_map * 2) x 16 x 16
            nn.Conv2d(self.feature_map * 2, self.feature_map * 4, 4, 2, 1, bias=bias),
            nn.BatchNorm2d(self.feature_map * 4),
            nn.LeakyReLU(0.2, inplace=True),
            # State size: (feature_map * 4) x 8 x 8
            nn.Conv2d(self.feature_map * 4, self.feature_map * 8, 4, 2, 1, bias=bias),
            nn.BatchNorm2d(self.feature_map * 8),
            nn.LeakyReLU(0.2, inplace=True),
            # Output size: (feature_map * 8) x 4 x 4
            nn.Conv2d(self.feature_map * 8, 1, 4, 1, 0, bias=bias),
            nn.Sigmoid()
        )

    def forward(self, input):
        """ Perform forward pass """
        return self.main(input)

    def define_optim(self, learning_rate, beta1):
        """ Initialize Loss Function and Optimizer """
        self.optimizer = optim.Adam(self.main.parameters(), lr=learning_rate, betas=(beta1, 0.999))

    @staticmethod
    def init_weights(layers):
        """ Randomly initialize weights from Normal distribution with mean = 0, std = 0.02 """
        classname = layers.__class__.__name__
        if classname.find('Conv') != -1:
            nn.init.normal_(layers.weight.data, 0.0, 0.02)
        elif classname.find('BatchNorm') != -1:
            nn.init.normal_(layers.weight.data, 1.0, 0.02)
            nn.init.constant_(layers.bias.data, 0)
