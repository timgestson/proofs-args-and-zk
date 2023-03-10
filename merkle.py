from hashlib import sha256


class Merkle:
    """Merkel Proofs for power of 2 leaf lengths"""

    def commit(leaves):
        if len(leaves) == 2:
            return sha256(leaves[0] + leaves[1]).digest()
        return Merkle.commit(
            [sha256(a + b).digest() for (a, b) in zip(leaves[::2], leaves[1::2])]
        )

    def hash_felts(felts):
        return [Merkle.hash_felt(felt) for felt in felts]

    def hash_felt(felt):
        return sha256(felt.val.to_bytes(16, "little", signed=False)).digest()

    def open(leaves, index, path=[]):
        if len(leaves) == 1:
            return path
        half = index // 2
        pairs = list(zip(leaves[::2], leaves[1::2]))
        return Merkle.open(
            [sha256(a + b).digest() for (a, b) in pairs],
            half,
            path + [pairs[half][1 - index % 2]],
        )

    def verify(root, index, leaf, path):
        half = index // 2
        if index % 2:
            next = sha256(path[0] + leaf).digest()
        else:
            next = sha256(leaf + path[0]).digest()
        if len(path) == 1:
            return next == root
        return Merkle.verify(root, half, next, path[1:])
