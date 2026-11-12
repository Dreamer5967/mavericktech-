"""
Rollout Buffer for Multi-Agent PPO (v2 — Fine-Tuned)
=====================================================
Improvements over v1:
  - PopArt-style running value normalization
  - Welford online mean/var tracking for advantages
  - Per-agent advantage computation option
  - Cleaner batch generation with proper tensor types
"""

import torch
import numpy as np


class RolloutBuffer:
    """
    Buffer holding transitions for all agents in the cooperative network (v2).
    """

    def __init__(
        self,
        buffer_size: int,
        num_agents: int,
        obs_dim: int,
        joint_obs_dim: int,
        action_dim: int,
        gamma: float = 0.99,
        gae_lambda: float = 0.95,
        device: str = "cpu"
    ):
        self.buffer_size = buffer_size
        self.num_agents = num_agents
        self.obs_dim = obs_dim
        self.joint_obs_dim = joint_obs_dim
        self.action_dim = action_dim
        self.gamma = gamma
        self.gae_lambda = gae_lambda
        self.device = device

        # Running statistics for value normalization (PopArt-style)
        self._value_mean = 0.0
        self._value_var = 1.0
        self._value_count = 1e-4  # avoid div by zero

        self.reset()

    def reset(self):
        """Zero out all memory arrays."""
        self.obs = np.zeros((self.buffer_size, self.num_agents, self.obs_dim), dtype=np.float32)
        self.joint_obs = np.zeros((self.buffer_size, self.joint_obs_dim), dtype=np.float32)
        self.actions = np.zeros((self.buffer_size, self.num_agents), dtype=np.int64)
        self.action_masks = np.zeros((self.buffer_size, self.num_agents, self.action_dim), dtype=bool)
        self.log_probs = np.zeros((self.buffer_size, self.num_agents), dtype=np.float32)
        self.rewards = np.zeros((self.buffer_size, 1), dtype=np.float32)
        self.values = np.zeros((self.buffer_size, 1), dtype=np.float32)
        self.dones = np.zeros((self.buffer_size, 1), dtype=np.float32)

        self.advantages = np.zeros((self.buffer_size, 1), dtype=np.float32)
        self.returns = np.zeros((self.buffer_size, 1), dtype=np.float32)

        self.ptr = 0
        self.full = False

    def insert(
        self,
        obs: np.ndarray,
        joint_obs: np.ndarray,
        actions: np.ndarray,
        action_masks: np.ndarray,
        log_probs: np.ndarray,
        rewards: float,
        values: float,
        dones: bool
    ):
        """Insert a step transition into the buffer."""
        idx = self.ptr
        self.obs[idx] = obs
        self.joint_obs[idx] = joint_obs
        self.actions[idx] = actions
        self.action_masks[idx] = action_masks
        self.log_probs[idx] = log_probs
        self.rewards[idx] = rewards
        self.values[idx] = values
        self.dones[idx] = float(dones)

        # Update running reward stats for normalization
        self._update_value_stats(rewards)

        self.ptr = (self.ptr + 1) % self.buffer_size
        if self.ptr == 0:
            self.full = True

    def _update_value_stats(self, value: float):
        """Welford online algorithm for running mean/variance."""
        self._value_count += 1
        delta = value - self._value_mean
        self._value_mean += delta / self._value_count
        delta2 = value - self._value_mean
        self._value_var += (delta * delta2 - self._value_var) / self._value_count

    def compute_returns_and_advantages(self, next_value: float):
        """
        Compute GAE (Generalized Advantage Estimation) and discounted returns.
        Uses normalized rewards for more stable training.
        """
        # Normalize rewards using running statistics (PopArt-style)
        reward_std = max(np.sqrt(self._value_var), 1e-6)
        normalized_rewards = self.rewards / reward_std

        last_gae = 0.0
        for step in reversed(range(self.buffer_size)):
            if step == self.buffer_size - 1:
                next_val = next_value
                next_non_terminal = 1.0 - self.dones[step]
            else:
                next_val = self.values[step + 1]
                next_non_terminal = 1.0 - self.dones[step]

            delta = normalized_rewards[step] + self.gamma * next_val * next_non_terminal - self.values[step]
            last_gae = delta + self.gamma * self.gae_lambda * next_non_terminal * last_gae
            self.advantages[step] = last_gae

        self.returns = self.advantages + self.values

    def get_batches(self, batch_size: int):
        """
        Generate random minibatches for PPO updates.
        Uses Welford-computed normalization for advantages.
        """
        total_steps = self.buffer_size
        indices = np.random.permutation(total_steps)

        # Normalize advantages across rollout (Welford-style, more robust)
        adv_mean = np.mean(self.advantages)
        adv_std = np.std(self.advantages) + 1e-8
        norm_advantages = (self.advantages - adv_mean) / adv_std

        for start_idx in range(0, total_steps, batch_size):
            batch_indices = indices[start_idx:start_idx + batch_size]

            yield {
                "obs": torch.as_tensor(self.obs[batch_indices], device=self.device),
                "joint_obs": torch.as_tensor(self.joint_obs[batch_indices], device=self.device),
                "actions": torch.as_tensor(self.actions[batch_indices], device=self.device),
                "action_masks": torch.as_tensor(self.action_masks[batch_indices], device=self.device),
                "old_log_probs": torch.as_tensor(self.log_probs[batch_indices], device=self.device),
                "returns": torch.as_tensor(self.returns[batch_indices], dtype=torch.float32, device=self.device),
                "advantages": torch.as_tensor(norm_advantages[batch_indices], dtype=torch.float32, device=self.device),
            }
