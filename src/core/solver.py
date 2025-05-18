import numpy as np

class RevisedSimplexSolver:
    def __init__(self, A, b, c, sense):
        """
        A: matriz de coeficientes (m x n)
        b: vector de términos independientes (m,)
        c: vector de costos (n,)
        sense: lista con los sentidos de las restricciones ('≤', '=', '≥')
        """
        self.A = np.array(A, dtype=float)
        self.b = np.array(b, dtype=float)
        self.c = np.array(c, dtype=float)
        self.sense = sense

        self.m, self.n = self.A.shape

        # Variables totales incluyendo artificiales
        self._add_slack_and_artificial_vars()

    def _add_slack_and_artificial_vars(self):
        """
        Modifica A, c, y crea variables slack y artificiales para manejar sentidos.
        """
        A = self.A
        b = self.b
        sense = self.sense

        slack_vars = 0
        artificial_vars = 0

        rows = []
        for i in range(self.m):
            row = list(A[i])
            if sense[i] == '≤':
                # Añadir variable slack positiva
                slack_col = [0]*self.m
                slack_col[i] = 1
                row += slack_col
                # No artificial
                artificial_col = [0]*self.m
                row += artificial_col
                slack_vars += 1
            elif sense[i] == '=':
                # No slack, solo artificial
                slack_col = [0]*self.m
                row += slack_col
                artificial_col = [0]*self.m
                artificial_col[i] = 1
                row += artificial_col
                artificial_vars += 1
            elif sense[i] == '≥':
                # Slack negativa + artificial positiva
                slack_col = [0]*self.m
                slack_col[i] = -1
                row += slack_col
                artificial_col = [0]*self.m
                artificial_col[i] = 1
                row += artificial_col
                slack_vars += 1
                artificial_vars += 1
            else:
                raise ValueError("Sentido desconocido: debe ser '≤', '=', '≥'")
            rows.append(row)

        # Convertir lista a numpy array
        A_mod = np.array(rows, dtype=float)

        # Ajustar c para nuevas variables (slack=0, artificial=1 en fase1)
        c_mod = np.zeros(A_mod.shape[1])
        # Artificiales al final de las columnas, con coef 1 para fase 1
        # Contar cuántas variables originales + slack y artificial
        n_original = self.n
        n_slack = slack_vars * self.m  # Este cálculo está sobredimensionado, se corrige abajo
        n_slack = slack_vars  # Solo un slack por restricción
        n_artificial = artificial_vars

        # Coeficientes originales + slack = 0 en fase 1
        # Artificiales = 1 en fase 1 para minimizar suma
        start_artificial = n_original + n_slack
        c_mod[start_artificial:start_artificial + n_artificial] = 1

        self.A = A_mod
        self.c = c_mod
        self.b = b
        self.n_total = A_mod.shape[1]

        # Guardar índices de variables artificiales para uso posterior
        self.artificial_indices = list(range(start_artificial, start_artificial + n_artificial))
        self.slack_indices = list(range(n_original, n_original + n_slack))

        # Base inicial: variables slack y artificiales
        self.B_indices = self.slack_indices + self.artificial_indices

    def _phase_one(self):
        """
        Fase 1: encontrar solución básica factible minimizando suma variables artificiales.
        """
        max_iterations = 1000
        iteration = 0

        A = self.A
        b = self.b
        c = self.c
        B_indices = self.B_indices.copy()

        while iteration < max_iterations:
            iteration += 1

            B = A[:, B_indices]
            N_indices = [j for j in range(self.n_total) if j not in B_indices]
            N = A[:, N_indices]

            try:
                B_inv = np.linalg.inv(B)
            except np.linalg.LinAlgError:
                print("Base singular en fase 1")
                return False

            x_B = B_inv @ b
            c_B = c[B_indices]
            c_N = c[N_indices]

            lambda_ = c_B @ B_inv
            reduced_costs = c_N - lambda_ @ N

            if all(rc >= -1e-10 for rc in reduced_costs):
                # Condición de optimalidad fase 1
                # Revisar si suma artificiales en base es cero
                sum_artificial = 0
                for i, idx in enumerate(B_indices):
                    if idx in self.artificial_indices:
                        if x_B[i] > 1e-8:
                            print("Solución infactible (artificiales positivas).")
                            return False
                        else:
                            sum_artificial += x_B[i]
                if sum_artificial > 1e-8:
                    print("Solución infactible (artificiales positivas).")
                    return False
                # Solución básica factible encontrada
                self.B_indices = B_indices
                return True

            # Elegir variable entrante
            entering_candidates = [(idx, rc) for idx, rc in enumerate(reduced_costs) if rc < -1e-10]
            entering_idx, _ = min(entering_candidates, key=lambda x: x[1])
            entering_var = N_indices[entering_idx]

            A_j = A[:, entering_var]
            d = B_inv @ A_j

            # Regla de razón mínima
            ratios = []
            for i in range(len(d)):
                if d[i] > 1e-10:
                    ratios.append(x_B[i] / d[i])
                else:
                    ratios.append(np.inf)

            min_ratio = min(ratios)
            if min_ratio == np.inf:
                print("Problema no acotado en fase 1")
                return False

            leaving_idx = ratios.index(min_ratio)
            leaving_var = B_indices[leaving_idx]

            # Actualizar base
            B_indices[leaving_idx] = entering_var

        print("Máximo de iteraciones alcanzado en fase 1")
        return False

    def _remove_artificial_vars(self):
        """
        Elimina variables artificiales de la base y del problema.
        """
        artificial_set = set(self.artificial_indices)
        # Quitar artificiales de la base
        new_B_indices = [idx for idx in self.B_indices if idx not in artificial_set]

        # Intentar reemplazar si base quedó incompleta
        candidates = [j for j in range(self.n) if j not in new_B_indices]
        while len(new_B_indices) < self.m:
            for cidx in candidates:
                trial_base = new_B_indices + [cidx]
                B = self.A[:, trial_base]
                try:
                    np.linalg.inv(B)
                    new_B_indices.append(cidx)
                    candidates.remove(cidx)
                    break
                except np.linalg.LinAlgError:
                    continue
            else:
                break

        self.B_indices = new_B_indices

        # Eliminar columnas artificiales de A y c
        keep_cols = [j for j in range(self.n_total) if j not in artificial_set]
        self.A = self.A[:, keep_cols]
        self.c = self.c[keep_cols]
        self.n_total = self.A.shape[1]

        # Ajustar índices base según columnas eliminadas
        idx_map = {}
        new_idx = 0
        for old_idx in range(self.n_total + len(artificial_set)):
            if old_idx not in artificial_set:
                idx_map[old_idx] = new_idx
                new_idx += 1

        self.B_indices = [idx_map[idx] for idx in self.B_indices if idx in idx_map]

    def _phase_two(self):
        """
        Fase 2: optimizar función objetivo original sin variables artificiales.
        """
        max_iterations = 1000
        iteration = 0

        A = self.A
        b = self.b
        c = self.c
        B_indices = self.B_indices.copy()
        N_indices = [j for j in range(self.n_total) if j not in B_indices]

        while iteration < max_iterations:
            iteration += 1

            B = A[:, B_indices]
            N = A[:, N_indices]

            try:
                B_inv = np.linalg.inv(B)
            except np.linalg.LinAlgError:
                print("Base singular en fase 2")
                return None

            x_B = B_inv @ b
            c_B = c[B_indices]
            c_N = c[N_indices]

            lambda_ = c_B @ B_inv
            reduced_costs = c_N - lambda_ @ N

            if all(rc >= -1e-10 for rc in reduced_costs):
                # Solución óptima encontrada
                x = np.zeros(self.n_total)
                for i, idx in enumerate(B_indices):
                    x[idx] = x_B[i]
                return x[:self.n]  # sólo variables originales

            entering_candidates = [(idx, rc) for idx, rc in enumerate(reduced_costs) if rc < -1e-10]
            entering_idx, _ = min(entering_candidates, key=lambda x: x[1])
            entering_var = N_indices[entering_idx]

            A_j = A[:, entering_var]
            d = B_inv @ A_j

            ratios = []
            for i in range(len(d)):
                if d[i] > 1e-10:
                    ratios.append(x_B[i] / d[i])
                else:
                    ratios.append(np.inf)

            min_ratio = min(ratios)
            if min_ratio == np.inf:
                print("Problema no acotado en fase 2")
                return None
            leaving_idx = ratios.index(min_ratio)
            leaving_var = B_indices[leaving_idx]

            B_indices[leaving_idx] = entering_var
            N_indices[entering_idx] = leaving_var

        print("Máximo de iteraciones alcanzado en fase 2")
        return None

    def solve(self):
        """
        Ejecuta la fase 1 y fase 2 para resolver el problema.
        """
        print("Iniciando fase 1...")
        feasible = self._phase_one()
        if not feasible:
            print("No se encontró solución básica factible.")
            return None

        print("Removiendo variables artificiales...")
        self._remove_artificial_vars()

        print("Iniciando fase 2...")
        solution = self._phase_two()
        if solution is None:
            print("No se encontró solución óptima.")
        else:
            print("Solución óptima encontrada.")
        return solution