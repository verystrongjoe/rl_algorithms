# -*- coding: utf-8 -*-
"""Run module for TD3 with PER on LunarLanderContinuous-v2.

- Author: Curt Park
- Contact: curt.park@medipixel.io
"""

import argparse

import gym
import torch
import torch.optim as optim

from algorithms.common.networks.mlp import MLP
from algorithms.common.noise import GaussianNoise
from algorithms.per.td3_agent import Agent

device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

# hyper parameters
hyper_params = {
    "GAMMA": 0.99,
    "TAU": 1e-3,
    "NOISE_STD": 1.0,
    "NOISE_CLIP": 0.5,
    "DELAYED_UPDATE": 2,
    "BUFFER_SIZE": int(1e5),
    "BATCH_SIZE": 128,
    "LR_ACTOR": 1e-4,
    "LR_CRITIC_1": 1e-3,
    "LR_CRITIC_2": 1e-3,
    "GAUSSIAN_NOISE_MIN_SIGMA": 1.0,
    "GAUSSIAN_NOISE_MAX_SIGMA": 1.0,
    "GAUSSIAN_NOISE_DECAY_PERIOD": 1000000,
    "PER_ALPHA": 0.5,
    "PER_BETA": 0.4,
    "PER_EPS": 1e-6,
    "WEIGHT_DECAY": 1e-6,
}


def run(env: gym.Env, args: argparse.Namespace, state_dim: int, action_dim: int):
    """Run training or test.

    Args:
        env (gym.Env): openAI Gym environment with continuous action space
        args (argparse.Namespace): arguments including training settings
        state_dim (int): dimension of states
        action_dim (int): dimension of actions

    """
    hidden_sizes_actor = [256, 256]
    hidden_sizes_critic = [256, 256]

    # create actor
    actor = MLP(
        input_size=state_dim,
        output_size=action_dim,
        hidden_sizes=hidden_sizes_actor,
        output_activation=torch.tanh,
    ).to(device)
    actor_target = MLP(
        input_size=state_dim,
        output_size=action_dim,
        hidden_sizes=hidden_sizes_actor,
        output_activation=torch.tanh,
    ).to(device)
    actor_target.load_state_dict(actor.state_dict())

    # create critic
    critic_1 = MLP(
        input_size=state_dim + action_dim,
        output_size=1,
        hidden_sizes=hidden_sizes_critic,
    ).to(device)
    critic_2 = MLP(
        input_size=state_dim + action_dim,
        output_size=1,
        hidden_sizes=hidden_sizes_critic,
    ).to(device)
    critic_target1 = MLP(
        input_size=state_dim + action_dim,
        output_size=1,
        hidden_sizes=hidden_sizes_critic,
    ).to(device)
    critic_target2 = MLP(
        input_size=state_dim + action_dim,
        output_size=1,
        hidden_sizes=hidden_sizes_critic,
    ).to(device)
    critic_target1.load_state_dict(critic_1.state_dict())
    critic_target2.load_state_dict(critic_2.state_dict())

    # create optimizers
    actor_optim = optim.Adam(
        actor.parameters(),
        lr=hyper_params["LR_ACTOR"],
        weight_decay=hyper_params["WEIGHT_DECAY"],
    )
    critic_optim1 = optim.Adam(
        critic_1.parameters(),
        lr=hyper_params["LR_CRITIC_1"],
        weight_decay=hyper_params["WEIGHT_DECAY"],
    )
    critic_optim2 = optim.Adam(
        critic_2.parameters(),
        lr=hyper_params["LR_CRITIC_2"],
        weight_decay=hyper_params["WEIGHT_DECAY"],
    )

    # noise instance to make randomness of action
    noise = GaussianNoise(
        args.seed,
        hyper_params["GAUSSIAN_NOISE_MIN_SIGMA"],
        hyper_params["GAUSSIAN_NOISE_MAX_SIGMA"],
        hyper_params["GAUSSIAN_NOISE_DECAY_PERIOD"],
    )

    # make tuples to create an agent
    models = (actor, actor_target, critic_1, critic_2, critic_target1, critic_target2)
    optims = (actor_optim, critic_optim1, critic_optim2)

    # create an agent
    agent = Agent(env, args, hyper_params, models, optims, noise)

    # run
    if args.test:
        agent.test()
    else:
        agent.train()