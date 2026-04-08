import numpy as np
import torch


def create_sequences(data, target_col_idx, seq_len):
    """
    Create sliding window sequences from scaled feature array.

    Args:
        data: numpy array of shape (n_samples, n_features)
        target_col_idx: index of the target column in data
        seq_len: number of time steps per sequence

    Returns:
        X: torch tensor (n_sequences, seq_len, n_features)
        y: torch tensor (n_sequences,)
    """
    X, y = [], []

    for i in range(len(data) - seq_len):
        X.append(data[i:i + seq_len])
        y.append(data[i + seq_len, target_col_idx])

    X = np.array(X)
    y = np.array(y)

    return torch.FloatTensor(X), torch.FloatTensor(y)