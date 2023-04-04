from itertools import product
from felt import Felt


def hypercube(n):
    return [list(i) for i in product([Felt(0), Felt(1)], repeat=n)]


def flatten(matrix):
    return [item for row in matrix for item in row]
