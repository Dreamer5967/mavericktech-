"""
Centralized Critic Network for MAPPO (v2 — Fine-Tuned)
======================================================
Improvements over v1:
  - Orthogonal initialization
  - LayerNorm + Tanh activations
  - Deeper network (3 hidden layers instead of 2)
  - Separate value head with small-gain init
"""

import numpy as np
import torch
import torch.nn as nn


def ortho_init(layer: nn.Linear, gain: float = np.sqrt(2)):
    """Orthogonal initialization — standard for PPO networks."""
    nn.init.orthogonal_(layer.weight, gain=gain)
    nn.init.constant_(layer.bias, 0.0)
    return layer


class CriticMLP(nn.Module):
    """
    Centralized value function network V(s) (v2).
    Deeper network with LayerNorm for more accurate value estimation.
    """

    def __init__(self, joint_obs_dim: int, hidden_dim: int = 128):
        super().__init__()
        self.joint_obs_dim = joint_obs_dim

        self.net = nn.Sequential(
            ortho_init(nn.Linear(joint_obs_dim, hidden_dim)),
            nn.LayerNorm(hidden_dim),
            nn.Tanh(),
            ortho_init(nn.Linear(hidden_dim, hidden_dim)),
            nn.LayerNorm(hidden_dim),
            nn.Tanh(),
            ortho_init(nn.Linear(hidden_dim, hidden_dim // 2)),
            nn.LayerNorm(hidden_dim // 2),
            nn.Tanh(),
        )
        # Value head with unit-gain init (outputs should start near 0)
        self.value_head = ortho_init(nn.Linear(hidden_dim // 2, 1), gain=1.0)

    def forward(self, joint_obs: torch.Tensor) -> torch.Tensor:
        """
        Forward pass estimating scalar state value.

        Args:
            joint_obs: [batch_size, joint_obs_dim]

        Returns:
            values: [batch_size, 1]
        """
        features = self.net(joint_obs)
        return self.value_head(features)
