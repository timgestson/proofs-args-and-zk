from abc import ABC
from felt import Felt
from lagrange import eval_from_points


class SumcheckProver(ABC):
    def starting_round(self) -> tuple[Felt, list[Felt]]:
        pass

    def execute_round(self, r: Felt) -> list[Felt]:
        pass


class SumcheckVerifier(ABC):
    def starting_round(self):
        pass

    def execute_round(self):
        pass

    def final_round(self):
        pass


class SumcheckProtocol:
    def __init__(
        self, prover: SumcheckProver, verifier: SumcheckVerifier, variables: int
    ):
        self.prover = prover
        self.verifier = verifier
        self.variables = variables

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


class SuperEfficientProver(SumcheckProver):
    def __init__(self, evals, c, degree):
        self.evals = evals
        self.c = c
        self.degree = degree

    def poly_evals(self) -> list[Felt]:
        half = len(self.evals) // 2
        return [
            sum(
                [
                    Felt(1 - i) * a + Felt(i) * b
                    for (a, b) in zip(self.evals[:half], self.evals[half:])
                ],
                Felt(0),
            )
            for i in range(self.degree + 1)
        ]

    def starting_round(self) -> tuple[Felt, list[Felt]]:
        return (self.c, self.poly_evals())

    def execute_round(self, r: Felt) -> list[Felt]:
        half = len(self.evals) // 2
        self.evals = [
            (Felt(1) - r) * a + r * b
            for (a, b) in zip(self.evals[:half], self.evals[half:])
        ]
        return self.poly_evals()


class SuperEfficientVerifier(SumcheckVerifier):
    def __init__(self, degree, oracle):
        self.degree = degree
        self.oracle = oracle
        self.rs = []
        self.g_r = None

    def starting_round(self, c, evals) -> Felt:
        g1 = eval_from_points(evals, Felt(0)) + eval_from_points(evals, Felt(1))
        assert c == g1
        r = Felt.random()
        self.rs.append(r)
        self.g_r = eval_from_points(evals, r)
        return r

    def execute_round(self, evals) -> Felt:
        gj = eval_from_points(evals, Felt(0)) + eval_from_points(evals, Felt(1))
        assert self.g_r == gj
        r = Felt.random()
        self.rs.append(r)
        self.g_r = eval_from_points(evals, r)
        return r

    def final_round(self):
        assert self.g_r == self.oracle(self.rs)
