from math import log2
from itertools import product
from felt import Felt
from util import hypercube


class MultiLinearExtension:
    def __init__(self, evals, F=Felt):
        self.evals = evals
        self.F = F

    @classmethod
    def from_zeros(cls, length, F=Felt):
        return cls([F(0) for _ in range(length)], F)

    @classmethod
    def from_polynomial(cls, poly, F=Felt):
        hc = hypercube(poly.vars, F)
        evals = [poly.eval(h) for h in hc]
        return cls(evals, F)

    @classmethod
    def from_wiring_predicate(cls, wires, length, F=Felt):
        ones = set()
        for w in wires:
            ones.add(int("".join(str(i) for i in w), 2))

        return cls(
            [
                F(1) if i in ones else F(0)
                for i in range(2**length)
            ],
            F,
        )

    def __repr__(self) -> str:
        n = int(log2(len(self.evals)))
        hc = [tuple(i) for i in product([0, 1], repeat=n)]
        return str({tuple(h): e for h, e in zip(hc, self.evals)})

    def __add__(self, other):
        assert len(self.evals) == len(other.evals)
        return self.__class__(
            [x + y for x, y in zip(self.evals, other.evals)], self.F
        )

    def __mul__(self, other):
        assert len(self.evals) == len(other.evals)
        return self.__class__(
            [x * y for x, y in zip(self.evals, other.evals)], self.F
        )

    def eval(self, point):
        def memo(r, n):
            if n == 1:
                return [(self.F(1) - r[0]), r[0]]
            return [
                x
                for expr in memo(r, n - 1)
                for x in [expr * (self.F(1) - r[n - 1]), expr * r[n - 1]]
            ]

        cache = memo(point, len(point))
        return sum([x * y for (x, y) in zip(self.evals, cache)], self.F(0))

    def hypercube_eval(self):
        n = int(log2(len(self.evals)))
        hc = hypercube(n, self.F)
        return sum([self.eval(h) for h in hc], self.F(0)) 
