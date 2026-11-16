import numpy as np

from reinforcement_learning.agent import DQNAgent, ReplayBuffer


def test_replay_buffer_tracks_samples():
    buffer = ReplayBuffer(capacity=10)

    for idx in range(5):
        state = np.array([0.0, 1.0, 2.0, 3.0], dtype=np.float32)
        buffer.push(state, idx % 2, 1.0, state, False)

    assert len(buffer) == 5
    sample = buffer.sample(3)
    assert len(sample) == 3


def test_agent_returns_valid_action():
    agent = DQNAgent(state_size=4, action_size=2, seed=7)
    state = np.array([0.1, -0.2, 0.5, -0.4], dtype=np.float32)
    action = agent.act(state, epsilon=0.0)

    assert 0 <= action < 2
