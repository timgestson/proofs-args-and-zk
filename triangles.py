from hashlib import sha256
from math import log2
from felt import Felt
from lagrange import eval_mle, eval_ule
from util import hypercube
from sumcheck import SumcheckProver, SumcheckVerifier


class TriangleProver:
    def __init__(self, a, a2, c):
        self.a = a
        self.a2 = a2
        self.c = c
        self.logn = int(log2(len(self.a)))
        self.transcript = TrianglesTranscript()
        self.transcript.write_a(self.a)

    def prove(self):
        p1 = SumcheckProver(
            self.a2,
            self.a,
            self.c,
            self.transcript.hashchain.copy(),
        )
        p1.prove()
        self.transcript.add_transcript(p1.transcript)

        rands = p1.transcript.randoms
        (i, j) = (rands[: len(rands) // 2], rands[len(rands) // 2 :])

        p2 = SumcheckProver(
            [eval_mle(self.a, i + hc) for hc in hypercube(self.logn // 2)],
            [eval_mle(self.a, hc + j) for hc in hypercube(self.logn // 2)],
            eval_mle(self.a2, i + j),
            p1.transcript.hashchain.copy(),
        )
        p2.prove()
        self.transcript.add_transcript(p2.transcript)

        k = p2.transcript.randoms
        q = self.line_subroutine(i + j, k + j, i + k)
        self.transcript.write_q(q)
        return self.transcript

    def line_subroutine(self, a, b, c):
        ts = list(zip(a, b, c))
        w = self.a
        q = [
            eval_mle(w, [eval_ule(t, Felt(i)) for t in ts])
            for i in range(0, 2 * self.logn + 1)
        ]
        return q


class TriangleVerifier:
    def __init__(self, transcript):
        self.transcript = transcript

    def verify(self):
        v1 = SumcheckVerifier(self.transcript.transcripts[0])
        v1.verify()

        v2 = SumcheckVerifier(self.transcript.transcripts[1])
        v2.verify()

        rands = self.transcript.transcripts[0].randoms
        (i, j) = (rands[: len(rands) // 2], rands[len(rands) // 2 :])
        k = self.transcript.transcripts[1].randoms

        prover1_round_v = self.transcript.transcripts[0].randoms[-1]
        prover2_round_v = self.transcript.transcripts[1].randoms[-1]
        prover1_round_gv = self.transcript.transcripts[0].evaluations[-1]
        prover2_round_gv = self.transcript.transcripts[1].evaluations[-1]
        claimed_a2 = self.transcript.transcripts[1].sum
        
        q = self.transcript.q
        w = self.transcript.a

        wa = eval_ule(q, Felt(0))
        wb = eval_ule(q, Felt(1))
        wc = eval_ule(q, Felt(2))

        ra = Felt.random()
        ts = list(zip(i + j, k + j, i + k))
        r = [eval_ule(t, ra) for t in ts]

        assert len(q) <= 2 * len(i + j) + 1
        assert eval_ule(q, ra) == eval_mle(w, r)

        assert wa * claimed_a2 == eval_ule(prover1_round_gv, prover1_round_v)
        assert wb * wc == eval_ule(prover2_round_gv, prover2_round_v)


class TrianglesTranscript:
    def __init__(self, hashchain=None):
        self.hashchain = hashchain or sha256()
        self.a = []
        self.transcripts = []
        self.q = []

    def write_a(self, lst):
        for f in lst:
            self.hashchain.update(f.val.to_bytes(8, "big"))
        self.a = lst

    def write_q(self, lst):
        for f in lst:
            self.hashchain.update(f.val.to_bytes(8, "big"))
        self.q = lst

    def randomness(self):
        return self.hashchain.digest()

    def add_transcript(self, transcript):
        self.transcripts.append(transcript)
        self.hashchain = transcript.hashchain.copy()
