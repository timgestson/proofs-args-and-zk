from math import ceil, log, log2
from random import choice
from felt import GLFelt


class Fri:
    def __init__(self, rate, queries, poly):
        self.poly = poly
        self.degree = len(poly)
        group_size = pow(2, ceil(log(int(1 / rate * self.degree)) / log(2)))
        self.l = GLFelt.roots_of_unity(group_size)
        half = len(self.l) // 2
        self.s_prime = {x: y for (x, y) in zip(self.l, self.l[half:] + self.l[:half])}
        self.commits = []
        self.rs = []
        self.queries = queries

    def execute(self):
        rounds = int(log2(len(self.poly)))
        poly = self.poly
        domain = self.l
        self.commits.append(
            dict(zip(domain, GLFelt.fft(Fri.zero_pad(poly, domain), domain)))
        )
        for _ in range(rounds):
            r = GLFelt.random()
            self.rs.append(r)
            domain = domain[::2]
            poly = self.commit(poly, r, domain)

        for _ in range(self.queries):
            s = choice(self.l)
            s_ = self.s_prime[s]
            for i in range(rounds):
                p = self.commits[i][s]
                p_ = self.commits[i][s_]
                s_2 = s**2
                assert Fri.next(s, s_, p, p_, self.rs[i]) == self.commits[i + 1][s_2]
                s = s_2
                s_ = self.s_prime[s]

    def commit(self, poly, r, domain):
        odds = [o * r for o in poly[1::2]]
        evens = poly[::2]
        p = Fri.zero_pad([o + e for (o, e) in zip(odds, evens)], domain)
        self.commits.append(dict(zip(domain, GLFelt.fft(p, domain))))
        return p

    def zero_pad(poly, domain):
        return poly + [GLFelt(0) for _ in range(len(domain) - len(poly))]

    def next(si, si_, pi, pi_, xi):
        return (xi - si) * (si_ - si).inv() * pi_ + (xi - si_) * (si - si_).inv() * pi


# Fri(.4, 50, [GLFelt(17),GLFelt(2),GLFelt(3),GLFelt(4), GLFelt(14), GLFelt(27)]).execute()
