from felt import Felt


def eval_ule(evals, r, Felt=Felt):
    """Evaluate univariate low-degree extension"""

    if 0 <= r.val < len(evals):
        return evals[r.val]

    total = Felt(0)
    multiplier = Felt(1)
    for k in range(1, len(evals)):
        multiplier *= (r - Felt(k)) * Felt(-k).inv()

    total += multiplier * evals[0]

    for i in range(1, len(evals)):
        multiplier *= (
            (r - Felt(i - 1))
            * (r - Felt(i)).inv()
            * Felt(i).inv()
            * Felt(-(len(evals) - i))
        )
        total += multiplier * evals[i]

    return total


def eval_mle(evals, point, Felt=Felt):
    """Evaluate multi-linear extension"""

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
