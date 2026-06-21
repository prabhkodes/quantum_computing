import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
import math
import random
from collections import Counter
from pyqubo import Array
import neal

# problem size
N = 10

# constant seed
SEED = 40

rng = np.random.default_rng(SEED) 
costs = np.round(rng.uniform(1.0, 10.0, size=N), 2)  

print(f'{costs = }\n')

B = float(np.round(0.50 * costs.sum(), 2))

SCALE = 100
B_int = int(round(B * SCALE))
costs_int = (costs * SCALE).astype(int)

print (f'{B = }')
print (f'{B_int = }')
print(f'{costs_int = }')
print('\n')

x = Array.create('x', shape=N, vartype='BINARY') 
m = int(math.ceil(math.log2(B_int + 1)))
y = Array.create('y', shape=m, vartype='BINARY')

total_cost = 0.0

for i in range(N):
    total_cost += costs_int[i] * x[i]

slack = 0.0
for k in range(m):
    slack += (2**k) * y[k]

A = 1.0 # penalty strength
constraint = A * ((total_cost + slack - B_int)**2) # Energy constraint
print(f'{constraint = }')

objective = 0 # Energy objective
for i in range(N):
    objective += -x[i]
print(f'{objective = }')

print(type(objective))
print(type(constraint))

H = objective + constraint # hamiltonian
print(f'{H = }')







