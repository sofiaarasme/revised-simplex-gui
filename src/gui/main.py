import tkinter as tk
from tkinter import messagebox, ttk
from src.core.solver import RevisedSimplexSolver

MAX_VARS = 20
MAX_CONS = 50
SENSES = ['≤', '=', '≥']

class SimplexGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Revised Simplex Solver")
        self.configure(bg="#F5F5F5")
        self.geometry("900x700")
        self._style_widgets()
        self._build_initial_frame()
        
    def _style_widgets(self):
        style = ttk.Style(self)
        style.theme_use('default')

        # Estilo general
        style.configure('TLabel', background='#F5F5F5', foreground='#000000', font=('Segoe UI', 12))
        style.configure('TEntry', font=('Segoe UI', 12))
        
        # Estilo de botones
        style.configure('Primary.TButton', font=('Segoe UI Semibold', 12), background='#005A9E', foreground='#FFFFFF', borderwidth=1, padding=5)
        style.map('Primary.TButton', background=[('active', '#004080')])

        style.configure('Secondary.TButton', font=('Segoe UI Semibold', 12), background='#28A745', foreground='#FFFFFF', borderwidth=1, padding=5)
        style.map('Secondary.TButton', background=[('active', '#218838')])

    def _build_initial_frame(self):
        frame = ttk.Frame(self, padding=20)
        frame.pack(pady=50)

        ttk.Label(frame, text="Cantidad de Variables:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.var_count = tk.IntVar(value=2)
        ttk.Spinbox(frame, from_=1, to=MAX_VARS, textvariable=self.var_count, width=10).grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(frame, text="Cantidad de Restricciones:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.cons_count = tk.IntVar(value=2)
        ttk.Spinbox(frame, from_=1, to=MAX_CONS, textvariable=self.cons_count, width=10).grid(row=1, column=1, padx=5, pady=5)

        button_frame = ttk.Frame(frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=15)

        ttk.Button(button_frame, text="Generar Modelo", style='Primary.TButton', command=self._on_generate).grid(row=0, column=0, padx=10)
        ttk.Button(button_frame, text="Limpiar", style='Secondary.TButton', command=self._clear_form).grid(row=0, column=1, padx=10)

    def _clear_form(self):
        for widget in self.winfo_children():
            widget.destroy()
        self._build_initial_frame()

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

        # Selector de objetivo
        objective_frame = ttk.Frame(container)
        objective_frame.pack(pady=10, fill=tk.X)
        ttk.Label(objective_frame, text="Objetivo:").pack(side=tk.LEFT, padx=5)
        self.objective = tk.StringVar(value="Maximizar")
        ttk.OptionMenu(objective_frame, self.objective, "Maximizar", "Maximizar", "Minimizar").pack(side=tk.LEFT)

        # Encabezado función objetivo
        ttk.Label(container, text="Función Objetivo:", font=('Segoe UI Semibold', 14)).pack(anchor=tk.W, pady=(10, 5))
        func_frame = ttk.Frame(container)
        func_frame.pack(anchor=tk.W, pady=5)
        self.obj_entries = []
        for j in range(n):
            e = ttk.Entry(func_frame, width=5)
            e.insert(0, "0")
            e.pack(side=tk.LEFT, padx=2)
            self.obj_entries.append(e)
            ttk.Label(func_frame, text=f"X{j+1}").pack(side=tk.LEFT, padx=2)
            if j < n - 1:
                ttk.Label(func_frame, text="+").pack(side=tk.LEFT, padx=2)

        # Encabezado restricciones
        ttk.Label(container, text="Restricciones:", font=('Segoe UI Semibold', 14)).pack(anchor=tk.W, pady=(20, 5))
        self.A_entries, self.b_entries, self.sense_vars = [], [], []
        for i in range(m):
            row_frame = ttk.Frame(container)
            row_frame.pack(anchor=tk.W, pady=5)
            row_entries = []
            for j in range(n):
                e = ttk.Entry(row_frame, width=5)
                e.insert(0, "0")
                e.pack(side=tk.LEFT, padx=2)
                row_entries.append(e)
                ttk.Label(row_frame, text=f"X{j+1}").pack(side=tk.LEFT, padx=2)
                if j < n - 1:
                    ttk.Label(row_frame, text="+").pack(side=tk.LEFT, padx=2)
            self.A_entries.append(row_entries)

            sense_var = tk.StringVar(value=SENSES[0])
            ttk.OptionMenu(row_frame, sense_var, SENSES[0], *SENSES).pack(side=tk.LEFT, padx=2)
            self.sense_vars.append(sense_var)

            be = ttk.Entry(row_frame, width=5)
            be.insert(0, "0")
            be.pack(side=tk.LEFT, padx=2)
            self.b_entries.append(be)

        # Botones de acción
        button_frame = ttk.Frame(container)
        button_frame.pack(pady=20)
        ttk.Button(button_frame, text="Resolver", style='Primary.TButton', command=self._on_solve).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="Limpiar", style='Secondary.TButton', command=self._clear_form).pack(side=tk.LEFT, padx=10)
        
        # Área de texto para mostrar el contenido del archivo simplex.log
        self.log_text = tk.Text(container, height=15, wrap=tk.WORD, state=tk.DISABLED, font=('Segoe UI', 12))
        self.log_text.pack(fill=tk.BOTH, expand=True, pady=10)

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

            # Leer y mostrar el contenido del archivo simplex.log
            self._display_log()

        except ValueError as ex:
            messagebox.showerror("Entrada inválida", str(ex))
            
    def _display_log(self):
        """Lee el archivo simplex.log y muestra su contenido en el área de texto."""
        try:
            with open("simplex.log", "r") as log_file:
                log_content = log_file.read()

            # Habilitar el widget de texto, insertar contenido y deshabilitarlo nuevamente
            self.log_text.config(state=tk.NORMAL)
            self.log_text.delete(1.0, tk.END)  # Limpiar contenido previo
            self.log_text.insert(tk.END, log_content)
            self.log_text.config(state=tk.DISABLED)
        except FileNotFoundError:
            messagebox.showerror("Error", "El archivo simplex.log no se encontró.")

if __name__ == '__main__':
    app = SimplexGUI()
    app.mainloop()
    