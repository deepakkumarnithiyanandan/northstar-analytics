# Reinforcement Learning Project

This project trains a Deep Q-Network (DQN) agent to solve the classic CartPole environment from Gymnasium. It is designed as a clean, beginner-friendly RL project with a minimal codebase, easy local setup, and a simple evaluation flow.

## Project goals

- Learn the core RL workflow: environment, policy, replay memory, and training loop.
- Train a DQN agent on a standard control task.
- Save a trained model checkpoint and evaluate it on new episodes.

## Environment

The project uses:

- `gymnasium` for the environment API
- `PyTorch` for the neural network and optimization
- `NumPy` for experience replay and reward tracking

The default task is `CartPole-v1`, which is a simple but effective benchmark for Q-learning and deep RL.

## Directory structure

```text
reinforcement_learning/
├── README.md
├── requirements.txt
├── __init__.py
├── config.py
├── agent.py
├── train.py
├── evaluate.py
├── checkpoints/
└── tests/
    └── test_agent.py
```

## Setup

From the repository root:

```powershell
cd reinforcement_learning
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Train the agent

```powershell
python train.py --episodes 500
```

This saves the trained model to `checkpoints/cartpole_dqn.pt` by default.

## Evaluate the agent

```powershell
python evaluate.py --model checkpoints/cartpole_dqn.pt --episodes 10
```

## Notes

- Training is deterministic enough for local experiments when using a fixed seed.
- The DQN implementation uses epsilon-greedy exploration and target-network stabilization.
- CartPole is a good first RL project because it shows the full loop of reward, experience replay, and policy updates without requiring a complex simulator.

## Future extensions

- Replace DQN with PPO or SAC for more advanced policy learning.
- Train on a custom environment that matches a business or robotics task.
- Add TensorBoard or Weights & Biases logging.
- Build a small dashboard to visualize reward curves.
