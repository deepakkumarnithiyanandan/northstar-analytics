import argparse
from pathlib import Path

import gymnasium as gym

from config import TrainingConfig
from agent import DQNAgent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train a DQN agent on CartPole.")
    parser.add_argument("--episodes", type=int, default=600, help="Number of training episodes.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed.")
    parser.add_argument("--render", action="store_true", help="Render the environment during training.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = TrainingConfig(
        seed=args.seed,
        max_episodes=args.episodes,
    )

    env = gym.make(config.env_id)
    state, _ = env.reset(seed=config.seed)
    state_size = env.observation_space.shape[0]
    action_size = env.action_space.n

    agent = DQNAgent(
        state_size=state_size,
        action_size=action_size,
        learning_rate=config.learning_rate,
        gamma=config.gamma,
        batch_size=config.batch_size,
        replay_capacity=config.replay_capacity,
        target_update_freq=config.target_update_freq,
        seed=config.seed,
    )

    save_path = Path(config.save_path)
    save_path.parent.mkdir(parents=True, exist_ok=True)

    epsilon = config.epsilon_start
    recent_rewards = []

    for episode in range(1, config.max_episodes + 1):
        state, _ = env.reset(seed=config.seed + episode)
        total_reward = 0.0

        for step in range(config.max_steps_per_episode):
            if args.render:
                env.render()

            action = agent.act(state, epsilon)
            next_state, reward, terminated, truncated, _ = env.step(action)
            done = terminated or truncated

            agent.remember(state, action, reward, next_state, done)
            loss = agent.train_step()

            state = next_state
            total_reward += reward

            if done:
                break

        epsilon = max(config.epsilon_end, epsilon * config.epsilon_decay)
        recent_rewards.append(total_reward)

        if episode % config.log_every == 0 or episode == 1:
            avg_reward = sum(recent_rewards[-config.log_every:]) / min(len(recent_rewards), config.log_every)
            print(
                f"Episode {episode:03d} | Reward: {total_reward:>5.1f} | "
                f"Average (last {min(len(recent_rewards), config.log_every)}): {avg_reward:>5.2f} | "
                f"Epsilon: {epsilon:>4.3f}"
            )

        if episode % 100 == 0:
            agent.save(str(save_path))

    env.close()
    final_model = str(save_path)
    agent.save(final_model)
    print(f"Training complete. Model saved to {final_model}")


if __name__ == "__main__":
    main()
