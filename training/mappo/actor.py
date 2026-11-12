"""
Shared Actor Network for MAPPO (v2 — Fine-Tuned)
=================================================
Improvements over v1:
  - Orthogonal weight initialization (PPO standard)
  - LayerNorm after each hidden layer for stable gradients
  - Tanh activations (smoother gradient flow than ReLU for RL)
  - Temperature-scaled action masking
"""

import torch
import torch.nn as nn
from torch.distributions.categorical import Categorical
import numpy as np


def ortho_init(layer: nn.Linear, gain: float = np.sqrt(2)):
    """Orthogonal initialization — standard for PPO networks."""
    nn.init.orthogonal_(layer.weight, gain=gain)
    nn.init.constant_(layer.bias, 0.0)
    return layer


class ActorMLP(nn.Module):
    """
    Decentralized actor policy network (v2).
    Shared across all junctions, conditioned on junction identity one-hot.
    """

    def __init__(self, obs_dim: int, action_dim: int, hidden_dim: int = 64):
        super().__init__()
        self.obs_dim = obs_dim
        self.action_dim = action_dim

        self.net = nn.Sequential(
            ortho_init(nn.Linear(obs_dim, hidden_dim)),
            nn.LayerNorm(hidden_dim),
            nn.Tanh(),
            ortho_init(nn.Linear(hidden_dim, hidden_dim)),
            nn.LayerNorm(hidden_dim),
            nn.Tanh(),
        )
        # Smaller init gain for the output layer (standard PPO practice)
        self.logits_layer = ortho_init(nn.Linear(hidden_dim, action_dim), gain=0.01)

    def forward(self, obs: torch.Tensor, action_mask: torch.Tensor = None) -> Categorical:
        """
        Forward pass producing a masked Categorical distribution.

        Args:
            obs: [batch_size, obs_dim]
            action_mask: [batch_size, action_dim] boolean mask (True = available)

        Returns:
            Categorical distribution over actions
        """
        features = self.net(obs)
        logits = self.logits_layer(features)

        if action_mask is not None:
            # Temperature-scaled masking: -1e8 is numerically safer than -inf
            very_negative = torch.tensor(-1e8, device=logits.device, dtype=logits.dtype)
            masked_logits = torch.where(
                action_mask.bool(),
                logits,
                very_negative
            )
            return Categorical(logits=masked_logits)

        return Categorical(logits=logits)

    def get_action(self, obs: np.ndarray, action_mask: np.ndarray = None, deterministic: bool = False):
        """
        Sample an action for inference / environment step.
        """
        device = self.logits_layer.weight.device
        with torch.no_grad():
            obs_t = torch.as_tensor(obs, dtype=torch.float32, device=device).unsqueeze(0)
            mask_t = None
            if action_mask is not None:
                mask_t = torch.as_tensor(action_mask, dtype=torch.bool, device=device).unsqueeze(0)

            dist = self.forward(obs_t, mask_t)
            if deterministic:
                action = torch.argmax(dist.probs, dim=-1)
            else:
                action = dist.sample()

            log_prob = dist.log_prob(action)
            return action.item(), log_prob.item()

    def evaluate_actions(self, obs: torch.Tensor, actions: torch.Tensor, action_mask: torch.Tensor = None):
        """
        Evaluate log-probs and entropy for PPO updates.
        """
        dist = self.forward(obs, action_mask)
        log_probs = dist.log_prob(actions)
        entropy = dist.entropy()
        return log_probs, entropy
