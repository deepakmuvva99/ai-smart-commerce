"""
Soft Actor-Critic (SAC) Reinforcement Learning Agent for Dynamic Pricing.
V5 Architecture -- upgraded to match the Colab training pipeline.

Changes vs V1:
  - state_dim=10 (adds demand prediction, uncertainty, promotion_flag, price_volatility)
  - hidden_dim=256 (larger capacity for richer state space)
  - buffer_capacity=300_000
  - Orthogonal weight init on Actor for stable gradients
  - Action range [0.70, 1.30] (tighter than old [0.7, 1.5])
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
import numpy as np
import os
import json
from collections import deque
import random


# ============================================================
# Neural Network Components (V5)
# ============================================================

class Actor(nn.Module):
    """
    Policy network with LayerNorm and orthogonal init.
    Outputs price multiplier in [0.70, 1.30] via tanh squashing.
    """
    LOG_STD_MIN = -20
    LOG_STD_MAX = 2

    def __init__(self, state_dim, action_dim=1, hidden_dim=256):
        super(Actor, self).__init__()
        self.net = nn.Sequential(
            nn.Linear(state_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.ReLU(),
        )
        self.mu_head = nn.Linear(hidden_dim, action_dim)
        self.log_std_head = nn.Linear(hidden_dim, action_dim)

        # Orthogonal init for stable learning
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.orthogonal_(m.weight, gain=np.sqrt(2))
                nn.init.zeros_(m.bias)
        nn.init.orthogonal_(self.mu_head.weight, gain=0.01)

    def forward(self, state):
        x = self.net(state)
        mu = self.mu_head(x)
        log_std = torch.clamp(self.log_std_head(x), self.LOG_STD_MIN, self.LOG_STD_MAX)
        return mu, log_std

    def sample(self, state):
        """Sample action using reparameterization trick."""
        mu, log_std = self.forward(state)
        std = log_std.exp()
        normal = torch.distributions.Normal(mu, std)
        x_t = normal.rsample()
        action = torch.tanh(x_t)
        log_prob = (normal.log_prob(x_t) - torch.log(1 - action.pow(2) + 1e-6)).sum(-1, keepdim=True)
        return action, log_prob, mu


class Critic(nn.Module):
    """Twin Q-Network for reduced overestimation bias."""
    def __init__(self, state_dim, action_dim=1, hidden_dim=256):
        super(Critic, self).__init__()
        self.q1 = nn.Sequential(
            nn.Linear(state_dim + action_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 1),
        )
        self.q2 = nn.Sequential(
            nn.Linear(state_dim + action_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 1),
        )

    def forward(self, state, action):
        x = torch.cat([state, action], dim=-1)
        return self.q1(x), self.q2(x)


# ============================================================
# Replay Buffer
# ============================================================

class ReplayBuffer:
    """Experience replay buffer for off-policy learning."""
    def __init__(self, capacity=300_000):
        self.buffer = deque(maxlen=capacity)

    def push(self, state, action, reward, next_state, done):
        self.buffer.append((state, action, reward, next_state, done))

    def sample(self, batch_size):
        batch = random.sample(self.buffer, min(batch_size, len(self.buffer)))
        states, actions, rewards, next_states, dones = zip(*batch)
        return (
            torch.FloatTensor(np.array(states)),
            torch.FloatTensor(np.array(actions)),
            torch.FloatTensor(np.array(rewards)).unsqueeze(1),
            torch.FloatTensor(np.array(next_states)),
            torch.FloatTensor(np.array(dones)).unsqueeze(1),
        )

    def __len__(self):
        return len(self.buffer)

    def save(self, path):
        """Persist buffer to disk for crash recovery."""
        data = list(self.buffer)
        with open(path, 'w') as f:
            json.dump([(s.tolist() if isinstance(s, np.ndarray) else s,
                        a if isinstance(a, (list, float)) else [a],
                        r,
                        ns.tolist() if isinstance(ns, np.ndarray) else ns,
                        d) for s, a, r, ns, d in data], f)

    def load(self, path):
        """Load buffer from disk."""
        if os.path.exists(path):
            with open(path, 'r') as f:
                data = json.load(f)
                for s, a, r, ns, d in data:
                    self.buffer.append((s, a, r, ns, d))


# ============================================================
# SAC Agent (V5)
# ============================================================

class SACAgent:
    """
    Soft Actor-Critic Agent for dynamic pricing (V5).

    State vector (10 dimensions):
      [current_price_norm, base_price_norm, inventory_norm,
       traffic_norm, sales_norm, predicted_demand_norm,
       prediction_uncertainty_norm, day_of_week_norm,
       promotion_flag, price_volatility_norm]

    Action (1 dimension):
      price_multiplier in [0.70, 1.30] (tighter band for stability)
    """

    ACTION_LOW  = 0.70
    ACTION_HIGH = 1.30

    def __init__(self, state_dim=10, action_dim=1, hidden_dim=256,
                 lr=3e-4, gamma=0.99, tau=0.005, alpha=0.2,
                 auto_entropy=True, buffer_capacity=300_000):
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.gamma = gamma
        self.tau = tau
        self.auto_entropy = auto_entropy

        # Networks
        self.actor = Actor(state_dim, action_dim, hidden_dim)
        self.critic = Critic(state_dim, action_dim, hidden_dim)
        self.critic_target = Critic(state_dim, action_dim, hidden_dim)
        self.critic_target.load_state_dict(self.critic.state_dict())

        # Optimizers
        self.actor_optimizer = optim.Adam(self.actor.parameters(), lr=lr)
        self.critic_optimizer = optim.Adam(self.critic.parameters(), lr=lr)

        # Automatic entropy tuning
        if auto_entropy:
            self.target_entropy = -float(action_dim)
            self.log_alpha = torch.zeros(1, requires_grad=True)
            self.alpha_optimizer = optim.Adam([self.log_alpha], lr=lr)
            self.alpha = self.log_alpha.exp().item()
        else:
            self.alpha = alpha

        # Replay buffer
        self.replay_buffer = ReplayBuffer(buffer_capacity)

        # Training stats
        self.total_updates = 0

    def select_action(self, state, evaluate=False):
        """Given a state vector, output a pricing action (multiplier)."""
        state_tensor = torch.FloatTensor(state).unsqueeze(0)

        if evaluate:
            with torch.no_grad():
                mu, _ = self.actor(state_tensor)
                action = torch.tanh(mu)
        else:
            with torch.no_grad():
                action, _, _ = self.actor.sample(state_tensor)

        # Scale from [-1, 1] to [ACTION_LOW, ACTION_HIGH]
        scaled = self.ACTION_LOW + (action.item() + 1.0) * 0.5 * (self.ACTION_HIGH - self.ACTION_LOW)
        return float(np.clip(scaled, self.ACTION_LOW, self.ACTION_HIGH))

    def store_transition(self, state, action, reward, next_state, done=False):
        """Store a (s, a, r, s', done) transition."""
        norm_action = 2.0 * (action - self.ACTION_LOW) / (self.ACTION_HIGH - self.ACTION_LOW) - 1.0
        self.replay_buffer.push(state, [norm_action], reward, next_state, float(done))

    def update(self, batch_size=256):
        """Perform one SAC update step."""
        if len(self.replay_buffer) < batch_size:
            return None

        states, actions, rewards, next_states, dones = self.replay_buffer.sample(batch_size)

        # ---- Critic Update ----
        with torch.no_grad():
            next_actions, next_log_probs, _ = self.actor.sample(next_states)
            q1_next, q2_next = self.critic_target(next_states, next_actions)
            q_next = torch.min(q1_next, q2_next) - self.alpha * next_log_probs
            q_target = rewards + self.gamma * (1 - dones) * q_next

        q1_pred, q2_pred = self.critic(states, actions)
        critic_loss = F.mse_loss(q1_pred, q_target) + F.mse_loss(q2_pred, q_target)

        self.critic_optimizer.zero_grad()
        critic_loss.backward()
        nn.utils.clip_grad_norm_(self.critic.parameters(), max_norm=1.0)
        self.critic_optimizer.step()

        # ---- Actor Update ----
        new_actions, log_probs, _ = self.actor.sample(states)
        q1_new, q2_new = self.critic(states, new_actions)
        q_new = torch.min(q1_new, q2_new)
        actor_loss = (self.alpha * log_probs - q_new).mean()

        self.actor_optimizer.zero_grad()
        actor_loss.backward()
        nn.utils.clip_grad_norm_(self.actor.parameters(), max_norm=1.0)
        self.actor_optimizer.step()

        # ---- Entropy Tuning ----
        alpha_loss = None
        if self.auto_entropy:
            alpha_loss = -(self.log_alpha * (log_probs + self.target_entropy).detach()).mean()
            self.alpha_optimizer.zero_grad()
            alpha_loss.backward()
            self.alpha_optimizer.step()
            self.alpha = self.log_alpha.exp().item()

        # ---- Soft Target Update ----
        for param, target_param in zip(self.critic.parameters(), self.critic_target.parameters()):
            target_param.data.copy_(self.tau * param.data + (1 - self.tau) * target_param.data)

        self.total_updates += 1
        return {
            "critic_loss": critic_loss.item(),
            "actor_loss": actor_loss.item(),
            "alpha": self.alpha,
            "alpha_loss": alpha_loss.item() if alpha_loss is not None else 0,
            "buffer_size": len(self.replay_buffer),
            "total_updates": self.total_updates,
        }

    def save(self, directory):
        """Save all model weights and buffer to disk."""
        os.makedirs(directory, exist_ok=True)
        torch.save(self.actor.state_dict(), os.path.join(directory, "sac_actor.pt"))
        torch.save(self.critic.state_dict(), os.path.join(directory, "sac_critic.pt"))
        torch.save(self.critic_target.state_dict(), os.path.join(directory, "sac_critic_target.pt"))
        self.replay_buffer.save(os.path.join(directory, "replay_buffer.json"))
        meta = {
            "total_updates": self.total_updates,
            "alpha": self.alpha,
            "state_dim": self.state_dim,
            "action_dim": self.action_dim,
        }
        with open(os.path.join(directory, "sac_meta.json"), 'w') as f:
            json.dump(meta, f, indent=2)

    def load(self, directory):
        """Load all model weights and buffer from disk."""
        actor_path = os.path.join(directory, "sac_actor.pt")
        if os.path.exists(actor_path):
            self.actor.load_state_dict(torch.load(actor_path, map_location='cpu'))
            self.critic.load_state_dict(torch.load(os.path.join(directory, "sac_critic.pt"), map_location='cpu'))
            self.critic_target.load_state_dict(torch.load(os.path.join(directory, "sac_critic_target.pt"), map_location='cpu'))
            self.replay_buffer.load(os.path.join(directory, "replay_buffer.json"))
            meta_path = os.path.join(directory, "sac_meta.json")
            if os.path.exists(meta_path):
                with open(meta_path, 'r') as f:
                    meta = json.load(f)
                    self.total_updates = meta.get("total_updates", 0)
            return True
        return False
