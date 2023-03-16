from math import prod
from felt import Felt


def eval_le(evals, r, Felt=Felt):
    numerator = set()
    denominator = set()

    def insert(term, inv=False):
        if not inv and term in denominator:
            denominator.remove(term)
        elif inv and term in numerator:
            numerator.remove(term)
        elif inv:
            denominator.add(term)
        else:
            numerator.add(term)

    def evaluate(r):
        return prod(
            [coef * r + const if coef.val else const for (coef, const) in numerator]
            + [
                (coef * r + const).inv() if coef.val else const.inv()
                for (coef, const) in denominator
            ],
            start=Felt(1),
        )

    total = Felt(0)

    for k in range(1, len(evals)):
        insert((Felt(1), Felt(-k)))
        insert((Felt(0), Felt(-k)), True)

    total += evaluate(r) * evals[0]

    for i in range(1, len(evals)):
        insert((Felt(1), Felt(0) - Felt(i - 1)))
        insert((Felt(1), Felt(-i)), True)
        insert((Felt(0), Felt(i)), True)
        insert((Felt(0), Felt(0) - Felt(len(evals) - i)))
        total += evaluate(r) * evals[i]

    return total


def eval_mle(evals, point, Felt=Felt):
    def memo(r, n):
        if n == 1:
            return [(Felt(1) - r[0]), r[0]]
        return [
            x
            for expr in memo(r, n - 1)
            for x in [expr * (Felt(1) - r[n - 1]), expr * r[n - 1]]
        ]

    cache = memo(point, len(point))
    return sum([x * y for (x, y) in zip(evals, cache)], Felt(0))
