from dataclasses import dataclass
from math import ceil, log, log2
from random import choice
from felt import GLFelt
from merkle import Merkle
from util import zero_pad


@dataclass
class FriOpening:
    index: int
    value: GLFelt
    path: list[bytes]


@dataclass
class FriCommitment:
    # root of the merkle tree
    root: str
    # domain element to index map
    domain_mapping: dict[GLFelt, int]
    # leaves
    leaves: list[bytes]
    # evals
    evals: list[GLFelt]

    @classmethod
    def commit(cls, evals, domain):
        leaves = Merkle.hash_felts(evals)
        root = Merkle.commit(leaves)
        dm = {d: i for (i, d) in enumerate(domain)}
        return cls(root, dm, leaves, evals)

    def open(self, element):
        index = self.domain_mapping[element]
        return FriOpening(index, self.evals[index], Merkle.open(self.leaves, index))


class FriProver:
    def __init__(self, poly, domain):
        self.l = domain
        self.rs = []
        self.polys = [poly]
        self.commits = []
        evals = GLFelt.fft(zero_pad(poly, len(domain), GLFelt), domain)
        self.commits.append(FriCommitment.commit(evals, domain))
        half = len(self.l) // 2
        self.s_prime = {x: y for (x, y) in zip(self.l, self.l[half:] + self.l[:half])}

    def commit(self, r):
        self.rs.append(r)
        poly = self.polys[-1]
        domain = self.l[:: 2 * len(self.rs)]
        odds = [o * r for o in poly[1::2]]
        evens = poly[::2]
        poly = zero_pad([o + e for (o, e) in zip(odds, evens)], len(domain), GLFelt)
        evals = GLFelt.fft(poly, domain)
        self.polys.append(poly)
        self.commits.append(FriCommitment.commit(evals, domain))
        return self.commits[-1].root

    def query(self, round, s):
        s_prime = self.s_prime[s]
        s_2 = s**2
        commit = self.commits[round]
        next_commit = self.commits[round + 1]
        return [commit.open(s), commit.open(s_prime), next_commit.open(s_2)]


class FriVerifier:
    def __init__(self, domain):
        self.merkle_roots = []
        self.rs = []
        self.s = None
        self.l = domain
        half = len(self.l) // 2
        self.s_prime = {x: y for (x, y) in zip(self.l, self.l[half:] + self.l[:half])}

    def commit(self, merkle_root, generate_random=True):
        self.merkle_roots.append(merkle_root)
        if generate_random:
            r = GLFelt.random()
            self.rs.append(r)
            return r

    def query(self):
        self.s = choice(self.l)
        return self.s

    def verify(self, round, openings):
        for opening in openings[:2]:
            assert Merkle.verify(
                self.merkle_roots[round],
                opening.index,
                Merkle.hash_felt(opening.value),
                opening.path,
            )
        assert Merkle.verify(
            self.merkle_roots[round + 1],
            openings[2].index,
            Merkle.hash_felt(openings[2].value),
            openings[2].path,
        )

        p = openings[0].value
        p_ = openings[1].value
        p2 = openings[2].value
        assert self.next(self.s, self.s_prime[self.s], p, p_, self.rs[round]) == p2
        self.s = self.s**2

    def next(self, si, si_, pi, pi_, xi):
        return (xi - si) * (si_ - si).inv() * pi_ + (xi - si_) * (si - si_).inv() * pi


class FriProtocol:
    def __init__(self, rate, queries, poly):
        self.degree = len(poly)
        group_size = pow(2, ceil(log(int(1 / rate * self.degree)) / log(2)))
        self.l = GLFelt.roots_of_unity(group_size)
        self.queries = queries
        self.prover = FriProver(poly, self.l)
        self.verifier = FriVerifier(self.l)
        self.rounds = int(log2(len(poly)))

    def execute(self):
        print("Commit")
        commit = self.prover.commits[-1].root
        for _ in range(self.rounds):
            r = self.verifier.commit(commit)
            commit = self.prover.commit(r)
        self.verifier.commit(commit, False)

        print("Query")
        for _ in range(self.queries):
            s = self.verifier.query()
            for i in range(self.rounds):
                openings = self.prover.query(i, s)
                self.verifier.verify(i, openings)
                s = s**2

        print("Success!")
