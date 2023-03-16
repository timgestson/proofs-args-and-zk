from math import log2
from felt import Felt
from lagrange import eval_le, eval_mle
from util import hypercube


class SumcheckProtocol:
    def __init__(self, c, evals, degree, oracle=None):
        self.prover = SumcheckProver(evals, c, degree)
        self.verifier = SumcheckVerifier(degree, oracle)
        self.variables = int(log2(len(evals)))

    def execute(self):
        (c, s1) = self.prover.starting_round()
        r = self.verifier.starting_round(c, s1)
        round = 1
        print("Round 1")
        if round == self.variables:
            self.verifier.final_round()
            print("Verified!")
            return self.verifier.rs
        while True:
            round += 1
            print("Round", round)
            s = self.prover.execute_round(r)
            r = self.verifier.execute_round(s)
            if round == self.variables:
                self.verifier.final_round()
                break
        print("Verfied!")
        return self.verifier.rs


class SumcheckProver:
    """Prover that is proving a Multilinear Polynomial"""

    def __init__(self, evals, c, degree):
        self.cache = evals
        self.c = c
        self.degree = degree

    def starting_round(self, Felt=Felt):
        return (self.c, self.poly_evals(Felt))

    def execute_round(self, r, Felt=Felt):
        half = len(self.cache) // 2
        self.cache = [
            (Felt(1) - r) * a + r * b
            for (a, b) in zip(self.cache[:half], self.cache[half:])
        ]
        return self.poly_evals(Felt)

    def poly_evals(self, Felt=Felt):
        half = len(self.cache) // 2
        return [
            sum(
                [
                    Felt(1 - i) * a + Felt(i) * b
                    for (a, b) in zip(self.cache[:half], self.cache[half:])
                ],
                Felt(0),
            )
            for i in range(self.degree + 1)
        ]


class SumcheckVerifier:
    def __init__(self, degree, oracle):
        self.degree = degree
        self.oracle = oracle
        self.rs = []
        self.g_r = None

    def starting_round(self, c, evals, Felt=Felt):
        g1 = eval_le(evals, Felt(0)) + eval_le(evals, Felt(1))
        assert c == g1
        r = Felt.random()
        self.rs.append(r)
        self.g_r = eval_le(evals, r, Felt)
        return r

    def execute_round(self, evals, Felt=Felt):
        gj = eval_le(evals, Felt(0), Felt) + eval_le(evals, Felt(1), Felt)
        assert self.g_r == gj
        r = Felt.random()
        self.rs.append(r)
        self.g_r = eval_le(evals, r, Felt)
        return r

    def final_round(self):
        if self.oracle:
            assert self.g_r == self.oracle(self.rs)
