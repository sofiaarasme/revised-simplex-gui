import tkinter as tk
from tkinter import messagebox, ttk
from src.core.solver import RevisedSimplexSolver

MAX_VARS = 50
MAX_CONS = 50
SENSES = ['≤', '=', '≥']

class SimplexGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Revised Simplex Solver")
        self.configure(bg="#FFFFFF")  # fondo blanco
        self.geometry("900x700")
        self._style_widgets()
        self._build_initial_frame()

    def _style_widgets(self):
        style = ttk.Style(self)
        style.theme_use('default')
        style.configure('TLabel', background='#FFFFFF', foreground='#000000', font=('Segoe UI', 11))
        style.configure('TEntry', font=('Segoe UI', 11))
        style.configure('TButton', background='#007ACC', foreground='#FFFFFF', font=('Segoe UI Semibold', 11), borderwidth=0)
        style.map('TButton', background=[('active', '#005A9E')])
        style.configure('TOptionMenu', background='#FFFFFF', foreground='#000000', font=('Segoe UI', 11))

    def _build_initial_frame(self):
        frame = ttk.Frame(self, padding=20)
        frame.pack(pady=50)

        ttk.Label(frame, text="Número de variables:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.var_count = tk.IntVar(value=2)
        ttk.Entry(frame, textvariable=self.var_count, width=7).grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(frame, text="Número de restricciones:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.cons_count = tk.IntVar(value=2)
        ttk.Entry(frame, textvariable=self.cons_count, width=7).grid(row=1, column=1, padx=5, pady=5)

        ttk.Button(
            frame,
            text="Generar formulario",
            command=self._on_generate
        ).grid(row=2, column=0, columnspan=2, pady=15)

    def _on_generate(self):
        n, m = self.var_count.get(), self.cons_count.get()
        if not (1 <= n <= MAX_VARS) or not (1 <= m <= MAX_CONS):
            messagebox.showerror(
                "Error de entrada",
                f"Ingresa entre 1 y {MAX_VARS} variables, y 1 y {MAX_CONS} restricciones."
            )
            return
        for widget in self.winfo_children():
            widget.destroy()
        self._style_widgets()
        self._build_form(n, m)

    def _build_form(self, n, m):
        container = ttk.Frame(self, padding=10)
        container.pack(fill=tk.BOTH, expand=True)

        # Encabezado función objetivo
        ttk.Label(container, text="Función objetivo (Max):", font=('Segoe UI Semibold', 13)).grid(row=0, column=0, columnspan=n+2, pady=(10,5), sticky=tk.W)
        self.obj_entries = []
        for j in range(n):
            e = ttk.Entry(container, width=8)
            e.insert(0, "0")
            e.grid(row=1, column=j, padx=4, pady=4)
            self.obj_entries.append(e)
            if j < n-1:
                ttk.Label(container, text="+").grid(row=1, column=j+ n, padx=2)

        # Encabezado restricciones
        ttk.Label(container, text="Restricciones:", font=('Segoe UI Semibold', 13)).grid(row=2, column=0, columnspan=n+2, pady=(20,5), sticky=tk.W)
        self.A_entries, self.b_entries, self.sense_vars = [], [], []
        for i in range(m):
            row_entries = []
            for j in range(n):
                e = ttk.Entry(container, width=8)
                e.insert(0, "0")
                e.grid(row=3+i, column=j, padx=4, pady=4)
                row_entries.append(e)
            self.A_entries.append(row_entries)

            sense_var = tk.StringVar(value=SENSES[0])
            ttk.OptionMenu(container, sense_var, SENSES[0], *SENSES).grid(row=3+i, column=n, padx=4)
            self.sense_vars.append(sense_var)

            be = ttk.Entry(container, width=8)
            be.insert(0, "0")
            be.grid(row=3+i, column=n+1, padx=4)
            self.b_entries.append(be)

        # Botón resolver
        ttk.Button(
            self,
            text="Resolver",
            command=self._on_solve
        ).pack(pady=20)

    def _on_solve(self):
        try:
            A = [[int(e.get()) for e in row] for row in self.A_entries]
            b = [int(e.get()) for e in self.b_entries]
            c = [int(e.get()) for e in self.obj_entries]
            sense = [sv.get() for sv in self.sense_vars]

            solver = RevisedSimplexSolver(A, b, c, sense)
            solution = solver.solve()
            if solution is None:
                messagebox.showinfo("Resultado", "No factible o no acotado.")
            else:
                res = "Solución óptima:\n"
                for i, val in enumerate(solution, start=1):
                    res += f"x{i} = {val:.2f}\n"
                messagebox.showinfo("Resultado", res)
        except ValueError as ex:
            messagebox.showerror("Entrada inválida", str(ex))

if __name__ == '__main__':
    app = SimplexGUI()
    app.mainloop()
