import torch
import torch.nn as nn


class Actor(nn.Module):

    def __init__(self, state_dim):

        super().__init__()

        self.net = nn.Sequential(
            nn.Linear(state_dim, 256),
            nn.ReLU(),
            nn.Linear(256, 256),
            nn.ReLU(),
            nn.Linear(256, 1)
        )

    def forward(self, x):

        return torch.tanh(self.net(x))