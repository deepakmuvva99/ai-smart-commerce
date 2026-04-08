import torch
import torch.nn as nn


class HybridDemandModel(nn.Module):

    def __init__(self, input_dim=15, d_model=64, heads=4, layers=2):

        super().__init__()

        self.embedding = nn.Linear(input_dim, d_model)

        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=heads,
            dim_feedforward=128,
            dropout=0.2,
            batch_first=True
        )

        self.transformer = nn.TransformerEncoder(
            encoder_layer,
            num_layers=layers
        )

        self.lstm = nn.LSTM(
            d_model,
            64,
            batch_first=True,
            bidirectional=True
        )

        self.attn = nn.Linear(128, 1)

        self.fc = nn.Sequential(
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(64, 1)
        )

    def forward(self, x):

        x = self.embedding(x)

        x = self.transformer(x)

        lstm_out, _ = self.lstm(x)

        weights = torch.softmax(self.attn(lstm_out), dim=1)

        context = (weights * lstm_out).sum(dim=1)

        return self.fc(context)