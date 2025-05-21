import numpy as np

class RevisedSimplexSolver:
    def __init__(self, A, b, c, sense):
        self.A = np.array(A, float)
        self.b = np.array(b, float)
        self.c_original = np.array(c, float)
        self.sense = sense
        self.m, self.n = self.A.shape
        self.steps = []
        self._add_slack_and_artificial_vars()

    def _log(self, msg):
        self.steps.append(msg)

    def _add_slack_and_artificial_vars(self):
        m, n = self.m, self.n
        A = self.A
        self._log(f"Inicial: A={A.tolist()}, b={self.b.tolist()}, c={self.c_original.tolist()}, sentidos={self.sense}")
        # construir S y Ar
        slack, art = [], []
        for i, s in enumerate(self.sense):
            e = np.zeros(m); e[i]=1
            if s == '≤': slack.append(e)
            elif s == '≥': slack.append(-e); art.append(e)
            elif s == '=': art.append(e)
        S = np.column_stack(slack) if slack else np.zeros((m,0))
        Ar = np.column_stack(art) if art else np.zeros((m,0))
        A_ext = np.hstack([A, S, Ar])
        total = A_ext.shape[1]
        # costos fase1 y fase2
        c1 = np.zeros(total); c1[n+S.shape[1]:] = 1
        c2 = np.concatenate([self.c_original, np.zeros(S.shape[1]+Ar.shape[1])])
        B = list(range(n, total))
        self.A, self.b = A_ext, self.b
        self.c1, self.c2 = c1, c2
        self.n_total = total; self.n_slack=S.shape[1]; self.n_art=Ar.shape[1]
        self.art_idx = list(range(n+self.n_slack, total))
        self.B = B.copy()
        self._log(f"Extendido: A_ext cols={total}, base inicial={self.B}")

    def _phase(self, c, maximize=False):
        A, b = self.A, self.b
        B = self.B.copy()
        for it in range(1, 1001):
            Bm = A[:, B]
            try:
                Binv = np.linalg.inv(Bm)
            except np.linalg.LinAlgError:
                self._log(f"Iter {it}: base singular -> abortando")
                return None, None
            xB = Binv.dot(b)
            N = [j for j in range(self.n_total) if j not in B]
            cB, cN = c[B], c[N]
            π = cB.dot(Binv)
            red = cN - π.dot(A[:, N])
            self._log(f"Iter {it}: xB={np.round(xB,4).tolist()}, red={np.round(red,4).tolist()}")
            # óptimo?
            if (red <= 1e-8).all() if maximize else (red >= -1e-8).all():
                self._log(f"Iter {it}: óptimo alcanzado")
                return B, xB
            # entrante
            candidates = [i for i,r in enumerate(red) if (r>1e-8 if maximize else r< -1e-8)]
            ent_i = min(candidates, key=lambda i: red[i])
            ent = N[ent_i]
            self._log(f"Iter {it}: entrante col {ent} (red={red[ent_i]:.4f})")
            d = Binv.dot(A[:, ent])
            ratios = [xB[i]/d[i] if d[i]>1e-8 else np.inf for i in range(len(d))]
            if all(r==np.inf for r in ratios):
                self._log(f"Iter {it}: no acotado detectado")
                return None, None
            leave_i = int(np.argmin(ratios)); leave=B[leave_i]
            self._log(f"Iter {it}: saliente col {leave} (razón={ratios[leave_i]:.4f})")
            B[leave_i] = ent
            self._log(f"Iter {it}: nueva base {B}")
        self._log("Máximas iteraciones alcanzadas")
        return None, None

    def solve_with_log(self):
        self.steps.clear()
        self._log("--- FASE 1: minimizar artificiales ---")
        B1, xB1 = self._phase(self.c1, maximize=False)
        if B1 is None:
            self._log("Fase 1 fallida: infactible o singular")
            return None, self.steps
        for i, bi in enumerate(B1):
            if bi in self.art_idx and xB1[i]>1e-8:
                self._log("Infactible tras fase 1")
                return None, self.steps
        # limpiar artificiales
        keep = list(range(self.n + self.n_slack))
        self.A = self.A[:, keep]
        self.c2 = self.c2[:len(keep)]
        self.n_total = self.A.shape[1]
        self.B = [keep.index(bi) for bi in B1 if bi< self.n + self.n_slack]
        self._log(f"Tras fase1 base={self.B}")
        self._log("--- FASE 2: optimizar objetivo original ---")
        B2, xB2 = self._phase(self.c2, maximize=True)
        if B2 is None:
            self._log("Fase 2 fallida: no acotado o singular")
            return None, self.steps
        x = np.zeros(self.n)
        for idx, bi in enumerate(B2):
            if bi < self.n: x[bi] = xB2[idx]
        self._log(f"Solución óptima: {np.round(x,4).tolist()}")
        return x, self.steps