from math import log2
from felt import Felt
from sumcheck import SumcheckProtocol
from lagrange import eval_le, eval_mle
from util import hypercube


class GKR:
    def __init__(self, evals, add_wire, mult_wire):
        self.evals = evals
        self.add_wire = add_wire
        self.mult_wire = mult_wire
        self.round = 0

    def parse_wire_predicate(self, wires, length, Felt=Felt):
        ones = set()
        for w in wires:
            ones.add(int(w))
        return [Felt(1) if i in ones else Felt(0) for i in range(2**length)]

    def constrain_to_line(self, w, b, c, ra):
        t1 = [b[0], c[0]]
        t2 = [b[1], c[1]]
        m = eval_le(
            [
                eval_mle(w, [eval_mle(t1, [Felt(i)]), eval_mle(t2, [Felt(i)])])
                for i in range(3)
            ],
            ra,
        )
        r = [eval_mle(t1, [ra]), eval_mle(t2, [ra])]
        return (r, m)

    def execute_protocol(self):
        (r, m) = self.first_round()
        self.round += 1

        while True:
            (r, m) = self.execute_round(r, m)
            self.round += 1
            if self.round == len(self.evals):
                break

        self.final_round(r, m)

    def first_round(self):
        g0 = self.evals[0]
        r = [Felt.random() for _ in range(int(log2(len(g0))))]
        return (r, eval_mle(g0, r))

    def execute_round(self, r, m):
        w = self.evals[self.round]
        width = int(len(w))
        add = self.parse_wire_predicate(self.add_wire[self.round - 1], len(r) + width)
        mult = self.parse_wire_predicate(self.mult_wire[self.round - 1], len(r) + width)
        half = width // 2

        g = [
            eval_mle(add, r + hc) * (eval_mle(w, hc[:half]) + eval_mle(w, hc[half:]))
            + eval_mle(mult, r + hc) * (eval_mle(w, hc[:half]) * eval_mle(w, hc[half:]))
            for hc in hypercube(width)
        ]

        r = SumcheckProtocol(m, g, 1).execute()

        # Evaluate 2 points at once via the line subroutine
        b = r[: len(r) // 2]
        c = r[len(r) // 2 :]

        # Choose random point constrained to the line
        ra = Felt.random()

        return self.constrain_to_line(w, b, c, ra)

    def final_round(self, r, m):
        w = self.evals[-1]
        assert m == eval_mle(w, r)
        print("Circuit Verified!")
