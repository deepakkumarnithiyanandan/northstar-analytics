import argparse

import gymnasium as gym

from agent import DQNAgent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate a trained DQN agent.")
    parser.add_argument("--model", type=str, default="checkpoints/cartpole_dqn.pt", help="Path to the trained model checkpoint.")
    parser.add_argument("--episodes", type=int, default=10, help="Number of evaluation episodes.")
    parser.add_argument("--seed", type=int, default=42, help="Evaluation seed.")
    parser.add_argument("--render", action="store_true", help="Render evaluation episodes.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    env = gym.make("CartPole-v1")
    env.reset(seed=args.seed)

    dummy_state, _ = env.reset(seed=args.seed)
    state_size = env.observation_space.shape[0]
    action_size = env.action_space.n

    agent = DQNAgent(state_size=state_size, action_size=action_size, seed=args.seed)
    agent.load(args.model)

    rewards = []

    for episode in range(1, args.episodes + 1):
        state, _ = env.reset(seed=args.seed + episode)
        total_reward = 0.0

        while True:
            if args.render:
                env.render()

            action = agent.act(state, epsilon=0.0)
            next_state, reward, terminated, truncated, _ = env.step(action)
            total_reward += reward
            state = next_state

            if terminated or truncated:
                break

        rewards.append(total_reward)
        print(f"Episode {episode:02d} | Reward: {total_reward:>5.1f}")

    env.close()
    average_reward = sum(rewards) / len(rewards)
    print(f"Average reward across {args.episodes} episodes: {average_reward:.2f}")


if __name__ == "__main__":
    main()
