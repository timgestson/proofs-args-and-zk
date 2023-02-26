from hashlib import sha256
from felt import Felt

def hash_felt_list(lst):
    hash = sha256(
        bytearray([i.val % 256 for i  in lst])
    ).digest()
    return Felt(int.from_bytes(hash,'big'))

def flatten(matrix):
    return [ item for row in matrix for item in row ]