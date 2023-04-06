from hashlib import sha256
from math import log2
from felt import Felt
from lagrange import eval_ule


class SumcheckProver:
    def __init__(self, p1, p2, c, randomness=None):
        self.rounds = int(log2(len(p1)))
        self.transcript = SumcheckTranscript(randomness)
        self.c = c
        self.p1 = p1
        self.p2 = p2
        self.rs = []

    def prove(self):
        self.transcript.write_degree(2)
        self.transcript.write_rounds(self.rounds)
        self.transcript.write_sum(self.c)
        self.starting_round()
        for _ in range(1, self.rounds + 1):
            r = Felt.from_randomness(self.transcript.randomness())
            self.transcript.write_random(r)
            self.execute_round(r)

    def starting_round(self):
        self.transcript.write_evaluations(self.evaluate_points())

    def execute_round(self, r):
        self.rs.append(r)
        half = len(self.p1) // 2
        self.p1 = [
            (Felt(1) - r) * a + r * b for (a, b) in zip(self.p1[:half], self.p1[half:])
        ]
        self.p2 = [
            (Felt(1) - r) * a + r * b for (a, b) in zip(self.p2[:half], self.p2[half:])
        ]
        self.transcript.write_evaluations(self.evaluate_points())

    def evaluate_points(self):
        if len(self.p1) == 1:
            return [Felt(0), self.p1[0] * self.p2[0], Felt(0)]

        half = len(self.p1) // 2
        zero, one, two = Felt(0), Felt(0), Felt(0)
        for i in range(half):
            zero += self.p1[i] * self.p2[i]
            one += self.p1[half + i] * self.p2[half + i]
            two += (Felt(2) * self.p1[half + i] - self.p1[i]) * (
                Felt(2) * self.p2[half + i] - self.p2[i]
            )
        return [zero, one, two]


class SumcheckVerifier:
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


class SumcheckTranscript:
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
