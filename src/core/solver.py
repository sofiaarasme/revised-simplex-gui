import numpy as np
import logging

# Configurar logging a archivo 'simplex.log'
logging.basicConfig(
    filename='simplex.log',
    filemode='w',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class RevisedSimplexSolver:
    def __init__(self, A, b, c, sense):
        self.A = np.array(A, dtype=float)
        self.b = np.array(b, dtype=float)
        self.c_original = np.array(c, dtype=float)
        self.sense = sense
        self.m, self.n = self.A.shape
        logging.debug(f"Init A={self.A.tolist()}, b={self.b.tolist()}, c={self.c_original.tolist()}, sense={sense}")
        self._add_slack_and_artificial_vars()

    def _add_slack_and_artificial_vars(self):
        m, n = self.m, self.n
        A = self.A
        slack_cols = []
        art_cols = []
        for i, s in enumerate(self.sense):
            e = np.zeros(m)
            e[i] = 1
            if s == '≤':
                slack_cols.append(e)
            elif s == '≥':
                slack_cols.append(-e)
                art_cols.append(e)
            elif s == '=':
                art_cols.append(e)
            else:
                raise ValueError("Sentido desconocido: debe ser '≤', '≥' o '='")
        S = np.column_stack(slack_cols) if slack_cols else np.zeros((m,0))
        Ar = np.column_stack(art_cols) if art_cols else np.zeros((m,0))
        A_ext = np.hstack([A, S, Ar])
        total = A_ext.shape[1]
        # Costos fase1: minimizar suma artificiales
        c1 = np.zeros(total)
        for j in range(n + S.shape[1], total):
            c1[j] = 1
        # Costos fase2: original + ceros slack + ceros artificial
        c2 = np.concatenate([self.c_original, np.zeros(S.shape[1] + Ar.shape[1])])
        # Base inicial: índices de slack y artificiales
        B = list(range(n, n + S.shape[1] + Ar.shape[1]))
        self.A = A_ext; self.b = self.b
        self.c1 = c1; self.c2 = c2
        self.n_total = total
        self.n_slack = S.shape[1]; self.n_art = Ar.shape[1]
        self.art_idx = list(range(n + self.n_slack, total))
        self.B = B
        logging.debug(f"A_ext={self.A.tolist()}")
        logging.debug(f"c1={self.c1.tolist()}, c2={self.c2.tolist()}")
        logging.debug(f"B init={self.B}")

    def _phase(self, c, maximize=False):
        A, b = self.A, self.b
        B = self.B.copy()
        for it in range(1000):
            Bm = A[:, B]
            try:
                Binv = np.linalg.inv(Bm)
            except np.linalg.LinAlgError:
                logging.error("Base singular (phase)")
                return None, None
            xB = Binv.dot(b)
            N = [j for j in range(self.n_total) if j not in B]
            cB = c[B]; cN = c[N]
            lam = cB.dot(Binv)
            red = cN - lam.dot(A[:, N])
            logging.debug(f"Iter{it}, xB={xB.tolist()}, red={red.tolist()}, max={maximize}")
            # condición óptima
            if maximize:
                if all(r <= 1e-8 for r in red):
                    return B, xB
            else:
                if all(r >= -1e-8 for r in red):
                    return B, xB
            # elegir entrante
            if maximize:
                ent_rel = [(i, r) for i, r in enumerate(red) if r > 1e-8]
            else:
                ent_rel = [(i, r) for i, r in enumerate(red) if r < -1e-8]
            ent_i, _ = min(ent_rel, key=lambda x: x[1])
            ent = N[ent_i]
            d = Binv.dot(A[:, ent])
            # razón mínima
            ratios = [xB[i]/d[i] if (maximize and d[i]>1e-8) or (not maximize and d[i]>1e-8) else np.inf for i in range(len(d))]
            logging.debug(f"Iter{it}, ratios={ratios}")
            if all(r==np.inf for r in ratios):
                logging.error("No acotado")
                return None, None
            leave_i = ratios.index(min(ratios))
            B[leave_i] = ent
        logging.error("Máx iter reached")
        return None, None

    def solve(self):
        logging.info("Start phase1")
        B1, xB1 = self._phase(self.c1, maximize=False)
        if B1 is None:
            logging.error("Phase1 failed")
            return None
        # verificar infactibilidad
        for i, bi in enumerate(B1):
            if bi in self.art_idx and xB1[i] > 1e-8:
                logging.error("Infactible after phase1")
                return None
        # remover artificiales
        B = [bi for bi in B1 if bi < self.n + self.n_slack]
        keep = list(range(self.n + self.n_slack))
        self.A = self.A[:, keep]
        self.c2 = self.c2[:len(keep)]
        self.n_total = self.A.shape[1]
        self.B = [keep.index(bi) for bi in B]
        logging.info(f"After remove art, B={self.B}")
        # fase2 max
        logging.info("Start phase2")
        B2, xB2 = self._phase(self.c2, maximize=True)
        if B2 is None:
            logging.error("Phase2 failed")
            return None
        x = np.zeros(self.n)
        for i, bi in enumerate(B2):
            if bi < self.n:
                x[bi] = xB2[i]
        logging.info(f"Solution x={x.tolist()}")
        return x
