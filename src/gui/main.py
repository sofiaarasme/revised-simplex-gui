import tkinter as tk
from tkinter import messagebox

from src.core.solver import RevisedSimplexSolver

MAX_VARS = 50
MAX_CONS = 50

class SimplexGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Revised Simplex Solver")
        self.configure(bg="#00FFFF")  # fondo aqua
        self.geometry("900x700")
        self._build_initial_frame()

    def _build_initial_frame(self):
        # Frame inicial para tamaño de problema
        self.initial_frame = tk.Frame(self, bg="#00FF00", padx=20, pady=20)  # verde
        self.initial_frame.pack(pady=30)

        tk.Label(self.initial_frame, text="Número de variables:", bg="#00FF00", fg="blue").grid(row=0, column=0, sticky=tk.W)
        self.var_count = tk.IntVar(value=2)
        tk.Entry(self.initial_frame, textvariable=self.var_count, width=5).grid(row=0, column=1)

        tk.Label(self.initial_frame, text="Número de restricciones:", bg="#00FF00", fg="blue").grid(row=1, column=0, sticky=tk.W)
        self.cons_count = tk.IntVar(value=2)
        tk.Entry(self.initial_frame, textvariable=self.cons_count, width=5).grid(row=1, column=1)

        tk.Button(
            self.initial_frame,
            text="Generar formulario",
            command=self._on_generate,
            bg="#0000FF", fg="white",
            activebackground="#0000AA"
        ).grid(row=2, column=0, columnspan=2, pady=10)

    def _on_generate(self):
        n = self.var_count.get()
        m = self.cons_count.get()
        if not (1 <= n <= MAX_VARS) or not (1 <= m <= MAX_CONS):
            messagebox.showerror(
                "Error de entrada",
                f"Variables 1-{MAX_VARS}, restricciones 1-{MAX_CONS}."
            )
            return
        self.initial_frame.destroy()
        self._build_form(n, m)

    def _build_form(self, n, m):
        # Frame para formulario
        self.form_frame = tk.Frame(self, bg="#00FF00", padx=10, pady=10)
        self.form_frame.pack(fill=tk.BOTH, expand=True)

        # Función objetivo
        tk.Label(self.form_frame, text="Función objetivo (max):", bg="#00FF00", fg="blue").grid(row=0, column=0, columnspan=n, sticky=tk.W)
        self.obj_entries = []
        for j in range(n):
            e = tk.Entry(self.form_frame, width=7)
            e.grid(row=1, column=j)
            e.insert(0, "0")
            self.obj_entries.append(e)
        tk.Label(self.form_frame, text="+").grid(row=1, column=n)
        tk.Label(self.form_frame, text="Z", bg="#00FF00").grid(row=1, column=n+1)

        # Restricciones
        tk.Label(self.form_frame, text="Restricciones:", bg="#00FF00", fg="blue").grid(row=2, column=0, pady=(20,5), sticky=tk.W)
        self.A_entries = []
        self.b_entries = []
        self.sense_vars = []
        senses = ['≤', '=', '≥']
        for i in range(m):
            row = []
            for j in range(n):
                e = tk.Entry(self.form_frame, width=7)
                e.grid(row=3+i, column=j)
                e.insert(0, "0")
                row.append(e)
            self.A_entries.append(row)
            var = tk.StringVar(value=senses[0])
            tk.OptionMenu(self.form_frame, var, *senses).grid(row=3+i, column=n)
            self.sense_vars.append(var)
            be = tk.Entry(self.form_frame, width=7)
            be.grid(row=3+i, column=n+1)
            be.insert(0, "0")
            self.b_entries.append(be)

        # Botón resolver
        tk.Button(
            self,
            text="Resolver",
            command=self._on_solve,
            bg="#0000FF", fg="white",
            activebackground="#0000AA"
        ).pack(pady=20)

    def _on_solve(self):
        try:
            # Validar entradas de A
            A = []
            for row in self.A_entries:
                A_row = []
                for e in row:
                    value = e.get()
                    if not value.isdigit():
                        raise ValueError("Las entradas de A deben ser números enteros.")
                    A_row.append(int(value))
                A.append(A_row)

            # Validar entradas de b
            b = []
            for e in self.b_entries:
                value = e.get()
                if not value.isdigit():
                    raise ValueError("Las entradas de b deben ser números enteros.")
                b.append(int(value))

            # Validar entradas de c
            c = []
            for e in self.obj_entries:
                value = e.get()
                if not value.isdigit():
                    raise ValueError("Las entradas de la función objetivo deben ser números enteros.")
                c.append(int(value))

            # Obtener los sentidos
            sense = [sv.get() for sv in self.sense_vars]

            # Resolver el problema
            solver = RevisedSimplexSolver(A, b, c, sense)
            solution = solver.solve()
            if solution is None:
                messagebox.showinfo("Resultado", "No factible o no acotado.")
            else:
                result_str = "Solución óptima:\n"
                for idx, val in enumerate(solution):
                    result_str += f"x{idx+1} = {val:.2f}\n"
                messagebox.showinfo("Resultado", result_str)
        except ValueError as e:
            messagebox.showerror("Error", str(e))

if __name__ == '__main__':
    app = SimplexGUI()
    app.mainloop()