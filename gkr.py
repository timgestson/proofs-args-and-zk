from math import log2
from felt import Felt
from sumcheck import SumcheckProtocol, SuperEfficientProver, SuperEfficientVerifier
from mle import MultiLinearExtension as MLE
from polynomial import eval_from_points
from hypercube import Hypercube

class GKR:
    def __init__(self, evals, add_wire, mult_wire):
        self.evals = evals
        self.add_wire = add_wire
        self.mult_wire = mult_wire
        self.round = 0

    def execute_protocol(self):
        (r, m) = self.first_round()
        self.round += 1

        while True:
            (r,m) = self.execute_round(r, m)
            self.round += 1
            if self.round == len(self.evals):
                break
        
        self.final_round(r,m)

    def first_round(self):
        g0 = MLE(self.evals[0])
        r = [ Felt.random() for _ in range(int(log2(len(g0.evals)))) ] 
        return (r, g0.eval(r))
    
    def execute_round(self,r,m):
        w = MLE(self.evals[self.round])
        width = int(len(w.evals))
        add = MLE.from_wiring_predicate(self.add_wire[self.round-1], len(r)+width)
        mult = MLE.from_wiring_predicate(self.mult_wire[self.round-1], len(r)+width)
        half = width // 2

        g = MLE([ 
            add.eval(r+hc) * (w.eval(hc[:half]) + w.eval(hc[half:])) +
            mult.eval(r+hc) * (w.eval(hc[:half]) * w.eval(hc[half:]))
            for hc in Hypercube(width)
        ])

        sc = SumcheckProtocol(
            verifier=SuperEfficientVerifier(2,lambda x: g.eval(x)),
            prover=SuperEfficientProver(g.evals,m,2),
            variables=int(log2(len(g.evals))),
        )
        r = sc.execute()

        # Evaluate 2 points at once via the line subroutine
        b = r[:len(r)//2]
        c = r[len(r)//2:]

        # Choose random point constrained to the line
        ra = Felt.random()
        
        t1 = MLE([b[0],c[0]])
        t2 = MLE([b[1],c[1]])
        wl = lambda x: w.eval([t1.eval([x]),t2.eval([x])])
        m = eval_from_points([wl(Felt(0)),wl(Felt(1)),wl(Felt(2))], ra)
        r = [t1.eval([ra]), t2.eval([ra])]

        return (r,m)

    
    def final_round(self, r, m):
        w = MLE(self.evals[-1])
        assert(m == w.eval(r))
        print("Circuit Verified!")
