import torch


def integrated_gradients(model, x, steps=50):

    baseline = torch.zeros_like(x)

    grads = 0

    for alpha in torch.linspace(0, 1, steps):

        x_step = baseline + alpha * (x - baseline)

        x_step.requires_grad_(True)

        out = model(x_step)

        out.backward()

        grads += x_step.grad

    return grads / steps