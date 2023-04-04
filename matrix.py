from hashlib import sha256
from math import log2
from felt import Felt
from lagrange import eval_ule

class MatMulProver:
    def __init__(self, a_evals, b_evals, c, randomness=None):
        self.rounds = int(log2(len(a_evals)))
        self.transcript = MatMulTranscript(randomness)
        self.c = c
        self.a = a_evals
        self.b = b_evals
        self.rs = []

    def prove(self):
        self.transcript.write_degree(2)
        self.transcript.write_rounds(self.rounds)
        self.transcript.write_sum(self.c)
        self.starting_round()
        for _ in range(1,self.rounds+1):
            r = Felt.from_randomness(self.transcript.randomness())
            self.transcript.write_random(r)
            self.execute_round(r)

    def starting_round(self):
        self.transcript.write_evaluations(self.evaluate_points())

    def execute_round(self, r):
        self.rs.append(r)
        half = len(self.a) // 2
        self.a = [
            (Felt(1) - r) * a + r * b for (a, b) in zip(self.a[:half], self.a[half:])
        ]
        self.b = [
            (Felt(1) - r) * a + r * b for (a, b) in zip(self.b[:half], self.b[half:])
        ]
        self.transcript.write_evaluations(self.evaluate_points())

    def evaluate_points(self):
        half = len(self.a) // 2
        zero = sum([a * b for (a, b) in zip(self.a[:half], self.b[:half])], Felt(0))
        one = sum([a * b for (a, b) in zip(self.a[half:], self.b[half:])], Felt(0))
        two = sum(
            [
                (Felt(2) * a1 - a0) * (Felt(2) * b1 - b0)
                for ((a0, b0), (a1, b1)) in zip(
                    zip(self.a[:half], self.b[:half]), zip(self.a[half:], self.b[half:])
                )
            ],
            Felt(0),
        )
        return [zero, one, two]


class MatMulVerifier:
    def __init__(self, transcript):
        self.transcript = transcript

    def verify(self):
        assert self.transcript.sum == eval_ule(
            self.transcript.evaluations[0], Felt(0)
        ) + eval_ule(self.transcript.evaluations[0], Felt(1))
        assert len(self.transcript.evaluations[0]) <= self.transcript.degree + 1

        for i in range(self.transcript.rounds):
            g_l = eval_ule(self.transcript.evaluations[i], self.transcript.randoms[i])
            assert len(self.transcript.evaluations[i + 1]) <= self.transcript.degree + 1
            g_r = eval_ule(self.transcript.evaluations[i + 1], Felt(0)) + eval_ule(
                self.transcript.evaluations[i + 1], Felt(1)
            )
            assert g_l == g_r


class MatMulTranscript:
    def __init__(self, hashchain=None):
        self.hashchain = hashchain or sha256()
        self.evaluations = []
        self.degree = None
        self.rounds = None
        self.randoms = []

    def write_evaluations(self, lst):
        for f in lst:
            self.hashchain.update(f.val.to_bytes(8, "big"))
        self.evaluations.append(lst)

    def write_sum(self, c):
        self.hashchain.update(c.val.to_bytes(8, "big"))
        self.sum = c

    def write_degree(self, d):
        self.hashchain.update(d.to_bytes(2, "big"))
        self.degree = d

    def write_random(self, r):
        self.hashchain.update(r.val.to_bytes(8, "big"))
        self.randoms.append(r)

    def write_rounds(self, rounds):
        self.hashchain.update(rounds.to_bytes(2, "big"))
        self.rounds = rounds

    def randomness(self):
        return self.hashchain.digest()
