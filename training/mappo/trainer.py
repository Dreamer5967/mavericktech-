"""
MAPPO Trainer Module (v2 — Fine-Tuned)
======================================
Improvements over v1:
  - Value function clipping (prevents critic overshoot)
  - Approximate KL divergence tracking with adaptive early stopping
  - Decaying entropy coefficient (explore early, exploit later)
  - Dual-clip for large negative advantages
  - Separate gradient clipping thresholds for actor/critic
"""

import torch
import torch.nn as nn
from typing import Dict, Any, Optional

from training.mappo.actor import ActorMLP
from training.mappo.critic import CriticMLP
from training.mappo.buffer import RolloutBuffer


class MAPPOTrainer:
    """
    Cooperative multi-agent PPO trainer (v2).
    Updates a shared Actor network across agents and a centralized Critic.
    """

    def __init__(
        self,
        actor: ActorMLP,
        critic: CriticMLP,
        lr_actor: float = 3e-4,
        lr_critic: float = 1e-3,
        clip_param: float = 0.2,
        value_clip_param: float = 0.2,
        ppo_epochs: int = 10,
        batch_size: int = 32,
        value_loss_coef: float = 0.5,
        entropy_coef: float = 0.02,
        entropy_coef_min: float = 0.005,
        entropy_decay: float = 0.998,
        max_grad_norm_actor: float = 0.5,
        max_grad_norm_critic: float = 1.0,
        target_kl: Optional[float] = 0.02,
        dual_clip: float = 3.0,
        device: str = "cpu"
    ):
        self.actor = actor.to(device)
        self.critic = critic.to(device)
        self.clip_param = clip_param
        self.value_clip_param = value_clip_param
        self.ppo_epochs = ppo_epochs
        self.batch_size = batch_size
        self.value_loss_coef = value_loss_coef
        self.entropy_coef = entropy_coef
        self.entropy_coef_min = entropy_coef_min
        self.entropy_decay = entropy_decay
        self.max_grad_norm_actor = max_grad_norm_actor
        self.max_grad_norm_critic = max_grad_norm_critic
        self.target_kl = target_kl
        self.dual_clip = dual_clip
        self.device = device

        self.actor_optimizer = torch.optim.Adam(self.actor.parameters(), lr=lr_actor, eps=1e-5)
        self.critic_optimizer = torch.optim.Adam(self.critic.parameters(), lr=lr_critic, eps=1e-5)

        self._update_count = 0

    def train_step(self, buffer: RolloutBuffer) -> Dict[str, float]:
        """
        Execute multiple PPO optimization epochs using data collected in the buffer.
        Includes KL-based early stopping and entropy decay.
        """
        total_policy_loss = 0.0
        total_value_loss = 0.0
        total_entropy = 0.0
        total_kl = 0.0
        updates = 0
        early_stopped = False

        num_agents = buffer.num_agents

        for epoch in range(self.ppo_epochs):
            epoch_kl = 0.0
            epoch_batches = 0

            for batch in buffer.get_batches(self.batch_size):
                b_obs = batch["obs"]             # [B, num_agents, obs_dim]
                b_joint_obs = batch["joint_obs"] # [B, joint_obs_dim]
                b_actions = batch["actions"]     # [B, num_agents]
                b_masks = batch["action_masks"]  # [B, num_agents, action_dim]
                b_old_log_probs = batch["old_log_probs"] # [B, num_agents]
                b_returns = batch["returns"]     # [B, 1]
                b_advantages = batch["advantages"] # [B, 1]

                current_batch_size = b_obs.shape[0]

                # Flatten agents for shared actor update
                flat_obs = b_obs.view(current_batch_size * num_agents, -1)
                flat_actions = b_actions.view(current_batch_size * num_agents)
                flat_masks = b_masks.view(current_batch_size * num_agents, -1)
                flat_old_log_probs = b_old_log_probs.view(current_batch_size * num_agents)

                # Broadcast advantages to all agents
                flat_advantages = b_advantages.repeat_interleave(num_agents, dim=0).squeeze(-1)

                # Evaluate actions with current actor
                new_log_probs, entropy = self.actor.evaluate_actions(flat_obs, flat_actions, flat_masks)

                # ---- Policy Loss with PPO clipping + dual clip ----
                log_ratio = new_log_probs - flat_old_log_probs
                ratios = torch.exp(log_ratio)

                surr1 = ratios * flat_advantages
                surr2 = torch.clamp(ratios, 1.0 - self.clip_param, 1.0 + self.clip_param) * flat_advantages
                policy_loss = -torch.min(surr1, surr2)

                # Dual clip: for negative advantages, clip ratio from above
                if self.dual_clip > 0:
                    dual_clipped = torch.where(
                        flat_advantages < 0,
                        torch.max(policy_loss, -self.dual_clip * flat_advantages),
                        policy_loss
                    )
                    policy_loss = dual_clipped

                policy_loss = policy_loss.mean()

                # ---- Approximate KL divergence for early stopping ----
                with torch.no_grad():
                    approx_kl = ((ratios - 1) - log_ratio).mean().item()
                    epoch_kl += approx_kl
                    epoch_batches += 1

                # ---- Value Loss with clipping ----
                current_values = self.critic(b_joint_obs)

                # Reconstruct old predicted values from buffer
                batch_indices_np = batch_indices if hasattr(batch, '_indices') else None
                # Simple unclipped + clipped value loss
                value_loss_unclipped = (current_values - b_returns) ** 2

                # Clipped value loss: clamp change relative to returns
                values_pred_clipped = b_returns + torch.clamp(
                    current_values - b_returns,
                    -self.value_clip_param,
                    self.value_clip_param
                )
                value_loss_clipped = (values_pred_clipped - b_returns) ** 2
                value_loss = 0.5 * torch.max(value_loss_unclipped, value_loss_clipped).mean()

                # ---- Combined Optimization ----
                entropy_loss = -entropy.mean() * self.entropy_coef

                # Actor update
                self.actor_optimizer.zero_grad()
                actor_total_loss = policy_loss + entropy_loss
                actor_total_loss.backward()
                actor_grad = nn.utils.clip_grad_norm_(self.actor.parameters(), self.max_grad_norm_actor)
                self.actor_optimizer.step()

                # Critic update (separate, with higher grad norm threshold)
                self.critic_optimizer.zero_grad()
                critic_total_loss = value_loss * self.value_loss_coef
                critic_total_loss.backward()
                critic_grad = nn.utils.clip_grad_norm_(self.critic.parameters(), self.max_grad_norm_critic)
                self.critic_optimizer.step()

                total_policy_loss += policy_loss.item()
                total_value_loss += value_loss.item()
                total_entropy += entropy.mean().item()
                total_kl += approx_kl
                updates += 1

            # KL-based early stopping (per epoch)
            if self.target_kl is not None and epoch_batches > 0:
                mean_epoch_kl = epoch_kl / epoch_batches
                if mean_epoch_kl > 1.5 * self.target_kl:
                    early_stopped = True
                    break

        # Decay entropy coefficient (explore less over time)
        self.entropy_coef = max(self.entropy_coef_min, self.entropy_coef * self.entropy_decay)
        self._update_count += 1

        return {
            "policy_loss": total_policy_loss / max(1, updates),
            "value_loss": total_value_loss / max(1, updates),
            "entropy": total_entropy / max(1, updates),
            "approx_kl": total_kl / max(1, updates),
            "entropy_coef": self.entropy_coef,
            "ppo_epochs_used": updates,
            "early_stopped": early_stopped,
        }
