from hashlib import sha256
from itertools import product
from felt import Felt


def hash_felt_list(lst):
    hash = sha256(bytearray([i.val % 256 for i in lst])).digest()
    return Felt(int.from_bytes(hash, "big"))


def hypercube(n, F=Felt):
    return [list(i) for i in product([F(0), F(1)], repeat=n)]


def flatten(matrix):
    return [item for row in matrix for item in row]


def zero_pad(poly, length, F=Felt):
    return poly + [F(0) for _ in range(length - len(poly))]
