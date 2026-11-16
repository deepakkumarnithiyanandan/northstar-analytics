from dataclasses import dataclass


@dataclass
class TrainingConfig:
    env_id: str = "CartPole-v1"
    seed: int = 42
    max_episodes: int = 600
    max_steps_per_episode: int = 500
    learning_rate: float = 1e-3
    gamma: float = 0.99
    epsilon_start: float = 1.0
    epsilon_end: float = 0.05
    epsilon_decay: float = 0.995
    batch_size: int = 64
    replay_capacity: int = 20000
    target_update_freq: int = 50
    save_path: str = "checkpoints/cartpole_dqn.pt"
    log_every: int = 25
