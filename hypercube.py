import itertools
from felt import Felt

class Hypercube(list):
    def __init__(self, n, prime=2**61-1):
        return super().__init__(list(i) for i in itertools.product([Felt(0,prime), Felt(1,prime)], repeat=n))
