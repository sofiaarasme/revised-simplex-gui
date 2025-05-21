import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from src.core.solver import RevisedSimplexSolver

MAX_VARS = 20
MAX_CONS = 50
SENSES = ['≤', '=', '≥']

class SimplexGUI(tb.Window):
    def __init__(self):
        super().__init__(themename="litera")  # Tema moderno
        self.title("Revised Simplex Solver")
        self.geometry("1000x700")
        tb.Style()  # Inicializa estilos
        self._build_initial_frame()

    def clear_widgets(self):
        for widget in self.winfo_children():
            widget.destroy()

    def _on_reset(self):
        """Volver a la pantalla inicial"""
        self._build_initial_frame()

    def _build_initial_frame(self):
        self.clear_widgets()
        # Cabecera y descripción
        header = tb.Label(self, text="Solver de Simplex Revisado", font=(None, 30, 'bold'), bootstyle="info")
        header.pack(pady=(20, 5))

        frame = tb.Frame(self, padding=20)
        frame.pack()

        tb.Label(frame, text="Cantidad de Variables:", font=(None, 12)).grid(row=0, column=0, sticky=tk.W, pady=5)
        self.var_count = tk.IntVar(value=2)
        tb.Spinbox(frame, from_=1, to=MAX_VARS, textvariable=self.var_count, width=5).grid(row=0, column=1, pady=5)

        tb.Label(frame, text="Cantidad de Restricciones:", font=(None, 12)).grid(row=1, column=0, sticky=tk.W, pady=5)
        self.cons_count = tk.IntVar(value=2)
        tb.Spinbox(frame, from_=1, to=MAX_CONS, textvariable=self.cons_count, width=5).grid(row=1, column=1, pady=5)

        btn_frame = tb.Frame(frame)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=15)
        tb.Button(btn_frame, text="Generar Modelo", bootstyle=(PRIMARY, "outline"), command=self._on_generate).grid(row=0, column=1, padx=10)
        tb.Button(btn_frame, text="Limpiar", bootstyle=(SECONDARY, "outline"), command=self._build_initial_frame).grid(row=0, column=0, padx=10)

    def _on_generate(self):
        n, m = self.var_count.get(), self.cons_count.get()
        if not (1 <= n <= MAX_VARS) or not (1 <= m <= MAX_CONS):
            messagebox.showerror("Error de entrada", f"Variables:1-{MAX_VARS}, Restricciones:1-{MAX_CONS}.")
            return
        self._build_form(n, m)

    def _build_form(self, n, m):
        self.clear_widgets()

        container = tb.Frame(self, padding=10)
        container.pack(fill=tk.BOTH, expand=True)

        # Objetivo
        obj_frame = tb.Frame(container)
        obj_frame.pack(fill=tk.X, pady=10)
        tb.Label(obj_frame, text="Objetivo:", font=(None, 12)).pack(side=tk.LEFT)
        self.objective = tk.StringVar(value="Maximizar")
        tb.OptionMenu(obj_frame, self.objective, "Maximizar", "Maximizar", "Minimizar").pack(side=tk.LEFT, padx=5)

        tb.Label(container, text="Función Objetivo:", font=(None, 14, 'bold')).pack(anchor=tk.W)
        fo_frame = tb.Frame(container)
        fo_frame.pack(anchor=tk.W, pady=5)
        # Etiqueta Z=
        tb.Label(fo_frame, text="Z =", font=(None, 12, 'bold')).pack(side=tk.LEFT, padx=(0,5))
        self.obj_entries = []
        for j in range(n):
            entry = tb.Entry(fo_frame, width=5)
            entry.insert(0, "0")
            entry.pack(side=tk.LEFT, padx=2)
            self.obj_entries.append(entry)
            tb.Label(fo_frame, text=f"X{j+1}").pack(side=tk.LEFT)
            if j < n-1:
                tb.Label(fo_frame, text="+").pack(side=tk.LEFT)

        # Restricciones
        tb.Label(container, text="Restricciones:", font=(None, 14, 'bold')).pack(anchor=tk.W, pady=(20,5))
        self.A_entries, self.b_entries, self.sense_vars = [], [], []
        for i in range(m):
            row = tb.Frame(container)
            row.pack(anchor=tk.W, pady=3)
            row_entries = []
            for j in range(n):
                e = tb.Entry(row, width=5)
                e.insert(0, "0")
                e.pack(side=tk.LEFT)
                row_entries.append(e)
                tb.Label(row, text=f"X{j+1}").pack(side=tk.LEFT)
                if j < n-1:
                    tb.Label(row, text="+").pack(side=tk.LEFT)
            self.A_entries.append(row_entries)
            sense = tk.StringVar(value=SENSES[0])
            tb.OptionMenu(row, sense, *SENSES).pack(side=tk.LEFT, padx=5)
            self.sense_vars.append(sense)
            be = tb.Entry(row, width=5)
            be.insert(0, "0")
            be.pack(side=tk.LEFT)
            self.b_entries.append(be)

        # Botones y log
        btnf = tb.Frame(container)
        btnf.pack(pady=15)
        tb.Button(btnf, text="Reiniciar", bootstyle=(DANGER, "outline"), command=self._build_initial_frame).pack(side=tk.LEFT, padx=5)
        tb.Button(btnf, text="Resolver", bootstyle=(SUCCESS, "outline"), command=self._on_solve).pack(side=tk.LEFT, padx=5)

        self.log_text = tb.Text(container, height=15, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True, pady=10)

    def _on_solve(self):
        try:
            A = [[float(e.get()) for e in row] for row in self.A_entries]
            b = [float(e.get()) for e in self.b_entries]
            c = [float(e.get()) for e in self.obj_entries]
            senses = [sv.get() for sv in self.sense_vars]

            solver = RevisedSimplexSolver(A, b, c, senses)
            x, steps = solver.solve_with_log()
            if x is None:
                messagebox.showwarning("Resultado", "No factible o no acotado.")
            else:
                # Crear el mensaje con "Solución Óptima:"
                sol_str = "Solución Óptima:\n\n"
                sol_str += "".join([f"x{i+1} = {val:.4f}\n" for i, val in enumerate(x)])
                
                # Mostrar el mensaje con un ícono de "check"
                messagebox.showinfo("Resultado", sol_str)
            
            # Mostrar pasos en el área de texto
            self.log_text.delete(1.0, tk.END)
            for s in steps:
                self.log_text.insert(tk.END, s + "\n")
        except Exception as ex:
            messagebox.showerror("Error", str(ex))

if __name__ == '__main__':
    app = SimplexGUI()
    app.mainloop()
