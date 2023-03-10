from felt import Felt


class Terms:
    def __init__(self, poly: set[tuple]):
        self.poly = set()
        constant = Felt(1)
        for coef, const, inv in poly:
            if coef.val == 0:
                if inv:
                    constant *= const.inv()
                else:
                    constant *= const
            else:
                self.poly.add((coef, const, inv))
        self.poly.add((Felt(0), constant, False))

    def __mul__(self, other):
        # Cancel out inverses while multiplying to reduce field ops
        new = set(self.poly)
        for coef, const, inv in other.poly:
            if (coef, const, not inv) in self.poly:
                new.remove((coef, const, not inv))
            else:
                new.add((coef, const, inv))

        return Terms(new)

    def eval(self, val):
        e = Felt(1)
        for coef, const, inv in self.poly:
            if inv:
                e *= (coef * val + const).inv()
            else:
                e *= coef * val + const
        return e


def eval_from_points(evals, r):
    poly = Terms([])
    for k in range(1, len(evals)):
        poly *= Terms({(Felt(1), Felt(-k), False), (Felt(0), Felt(-k), True)})
    sum = poly.eval(r) * evals[0]
    for i in range(1, len(evals)):
        poly *= Terms(
            {
                (Felt(1), Felt(0) - Felt(i - 1), False),
                (Felt(1), Felt(-i), True),
                (Felt(0), Felt(i), True),
                (Felt(0), Felt(0) - Felt(len(evals) - i), False),
            }
        )
        sum += poly.eval(r) * evals[i]
    return sum
