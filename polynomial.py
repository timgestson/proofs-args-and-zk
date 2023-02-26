from collections import defaultdict
from dataclasses import dataclass
from felt import Felt

class MultiVariatePolynomial:
    def __init__(self, poly: dict[tuple[int],Felt], prime: int=2**61-1):
        self.poly = poly
        self.vars = len(list(self.poly.keys())[0]) if poly else 0
        self.prime = prime

    def __add__(self, other):
        new = defaultdict(lambda: Felt(0,self.prime))
        for k,v in self.poly.items():
            new[k]+=v
        for k,v in other.poly.items():
            new[k]+=v
        return self.__class__(dict(new), self.prime)

    def __mul__(self, other):
        new = defaultdict(lambda: Felt(0, self.prime))
        for ki, vi in self.poly.items():
            for kj, vj in other.poly.items():
                nj = tuple(sum(x) for x in zip(ki, kj))
                new[nj] += (vi * vj)
        return self.__class__(dict(new), self.prime)


    def eval(self, vals):
        new = defaultdict(lambda: Felt(0,self.prime))
        for expr, coef in self.poly.items():
            newExpr = []
            newCoef = Felt(coef.val,coef.prime)
            for i in range(len(expr)):
                if vals[i] is not None:
                    newCoef *= vals[i]**expr[i]
                else:
                    newExpr.append(expr[i])
            new[tuple(newExpr)] += newCoef
        if () in new:
            return new[()]
        return self.__class__(dict(new), self.prime)

    def __repr__(self) -> str:
        return str(self.poly)


# Univariate Polynomial Terms
class Terms:
    def __init__(self, poly: set[tuple], prime=2**61-1):
        self.poly = set()
        self.prime = prime
        constant = Felt(1, prime)
        for (coef,const,inv) in poly:
            if coef.val == 0:
                if inv:
                    constant *= const.inv()
                else:
                    constant *= const
            else:
                self.poly.add((coef,const,inv))
        self.poly.add((Felt(0, prime),constant,False))
    
    def __mul__(self, other):
        new = set(self.poly)
        for (coef, const, inv) in other.poly:
            if (coef, const, not inv) in self.poly:
                new.remove((coef, const, not inv))
            else:
                new.add((coef, const, inv))

        return Terms(new, self.prime)

    def eval(self, val):
        e = Felt(1,self.prime)
        for (coef, const, inv) in self.poly:
            if inv:
                e *= (coef * val + const).inv()
            else:
                e *= (coef * val + const)
        return e


def eval_from_points(evals, r):
    poly = Terms([])
    for k in range(1, len(evals)):
        poly *= Terms({
            (Felt(1),Felt(-k),False),
            (Felt(0),Felt(-k),True)
        })
    sum = poly.eval(r) * evals[0]
    for i in range(1, len(evals)):
        poly *= Terms({
            (Felt(1), Felt(0)-Felt(i-1),False),
            (Felt(1), Felt(-i),True),
            (Felt(0), Felt(i),True),
            (Felt(0), Felt(0)-Felt(len(evals)-i),False)
        })
        sum += poly.eval(r) * evals[i]
    return sum
