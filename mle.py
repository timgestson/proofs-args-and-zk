from math import log2
from itertools import product
from felt import Felt
from hypercube import Hypercube


class MultiLinearExtension:
    def __init__(self, evals, prime=2**61 - 1):
        self.evals = evals
        self.prime = prime

    @classmethod
    def from_zeros(cls, length, prime=2**61 - 1):
        return cls([Felt(0, prime) for _ in range(length)], prime)

    @classmethod
    def from_polynomial(cls, poly, prime=2**61 - 1):
        hc = Hypercube(poly.vars, prime)
        evals = [poly.eval(h) for h in hc]
        return cls(evals, prime)

    @classmethod
    def from_wiring_predicate(cls, wires, length, prime=2**61 - 1):
        ones = set()
        for w in wires:
            ones.add(int("".join(str(i) for i in w), 2))

        return cls(
            [
                Felt(1, prime) if i in ones else Felt(0, prime)
                for i in range(2**length)
            ],
            prime,
        )

    def __repr__(self) -> str:
        n = int(log2(len(self.evals)))
        hc = [tuple(i) for i in product([0, 1], repeat=n)]
        return str({tuple(h): e for h, e in zip(hc, self.evals)})

    def __add__(self, other):
        assert len(self.evals) == len(other.evals)
        return self.__class__(
            [x + y for x, y in zip(self.evals, other.evals)], self.prime
        )

    def __mul__(self, other):
        assert len(self.evals) == len(other.evals)
        return self.__class__(
            [x * y for x, y in zip(self.evals, other.evals)], self.prime
        )

    def eval(self, point):
        def memo(r, n):
            if n == 1:
                return [(Felt(1, self.prime) - r[0]), r[0]]
            return [
                x
                for expr in memo(r, n - 1)
                for x in [expr * (Felt(1, self.prime) - r[n - 1]), expr * r[n - 1]]
            ]

        cache = memo(point, len(point))
        return sum([x * y for (x, y) in zip(self.evals, cache)], Felt(0, self.prime))

    def hypercube_eval(self):
        n = int(log2(len(self.evals)))
        hc = Hypercube(n, self.prime)
        return sum([self.eval(h) for h in hc], Felt(0, self.prime))
