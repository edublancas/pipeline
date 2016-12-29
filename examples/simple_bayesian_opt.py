import matplotlib.pyplot as plt

import numpy as np
from robo.fmin import bayesian_optimization

import logging
logging.basicConfig(level=logging.INFO)


def fn(x):
    y = np.sin(3 * x[0]) * 4 * (x[0] - 1) * (x[0] + 2)
    return y


lower = np.array([-2])
upper = np.array([3])


bo = bayesian_optimization(fn, lower, upper, num_iterations=10)

for it in bo:
    print(it)


bo.incumbents
bo.incumbents_values

plt.plot(range(len(bo.incumbents_values)), bo.incumbents_values)

fn([150])