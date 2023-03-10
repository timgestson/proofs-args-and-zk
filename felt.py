import random


class Felt:
    def __init__(self, val, prime=2**61 - 1):
        self.val = val % prime
        self.prime = prime

    @classmethod
    def random(cls, prime=2**61 - 1):
        return cls(random.randrange(0, prime), prime)

    def __add__(self, felt):
        assert self.prime == felt.prime
        return Felt((self.val + felt.val) % self.prime, self.prime)

    def __sub__(self, felt):
        assert self.prime == felt.prime
        return Felt((self.val - felt.val) % self.prime, self.prime)

    def inv(self):
        # TODO: Extended Euclidean Algorithm
        if self.val == 0:
            return Felt(0, self.prime)
        return self ** (self.prime - 2)

    def __mul__(self, felt):
        assert self.prime == felt.prime
        return Felt((self.val * felt.val) % self.prime, self.prime)

    def __pow__(self, degree):
        n = degree % (self.prime - 1)
        num = pow(self.val, n, self.prime)
        return Felt(num, self.prime)

    def __eq__(self, other):
        return self.val == other.val

    def __repr__(self):
        return f"Felt({str(self.val)},{str(self.prime)})"

    def __hash__(self):
        return hash(str(self))


class GLFelt(Felt):
    """Goldilocks Feild 2^64-2-32+1 with 2^32 roots"""

    def __init__(self, val, _=None):
        super().__init__(val, 0xFFFFFFFF00000001)

    def roots_of_unity(n):
        root = GLFelt(1753635133440165772)
        order = 2**32
        while order != n:
            root = root**2
            order = order / 2
        return [root**x for x in range(n)]

    def fft(vals, domain):
        if len(vals) == 1:
            return vals

        odds = GLFelt.fft(vals[1::2], domain[::2])
        evens = GLFelt.fft(vals[::2], domain[::2])
        ans = [GLFelt(0)] * len(vals)
        length = len(odds)
        for i, (o, e) in enumerate(zip(odds, evens)):
            ans[i] = e + domain[i] * o
            ans[i + length] = e - domain[i] * o
        return ans
