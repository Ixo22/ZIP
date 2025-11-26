import tkinter as tk
from tkinter import messagebox
import threading
import time

class ZipSolverInteractive:
    def __init__(self, root):
        self.root = root
        self.root.title("Solver ZIP - Edición Interactiva & Gradiente")
        self.root.configure(bg="#f0f2f5") 

        self.FILAS = 7
        self.COLS = 7
        self.CELL_SIZE = 60 

        # --- ESTADO INTERNO ---
        self.grid_state = [[0 for _ in range(self.COLS)] for _ in range(self.FILAS)]
        self.cell_labels = [[None for _ in range(self.COLS)] for _ in range(self.FILAS)]
        self.next_number_to_place = 1

        self.crear_interfaz()

    def crear_interfaz(self):
        # Panel izquierdo 
        left_panel = tk.Frame(self.root, bg="#f0f2f5", padx=20, pady=20)
        left_panel.pack(side=tk.LEFT, fill=tk.Y)

        tk.Label(left_panel, text="Instrucciones:", font=("Arial", 12, "bold"), bg="#f0f2f5").pack(anchor="w")
        instr_text = (
            "• Clic en Vacío → Pone número.\n"
            "• Clic en Número → Pone Muro (X).\n"
            "• Clic en Muro → Borra."
        )
        tk.Label(left_panel, text=instr_text, font=("Arial", 10), justify=tk.LEFT, bg="#f0f2f5", pady=10).pack(anchor="w")

        # --- CORRECCIÓN AQUÍ: Cambiado 'py=10' por 'pady=10' ---
        btn_solve = tk.Button(left_panel, text="RESOLVER", command=self.iniciar_thread_solver, 
                              bg="#0a66c2", fg="white", font=('Arial', 14, 'bold'), cursor="hand2", pady=10)
        btn_solve.pack(fill=tk.X, pady=(20, 10))

        btn_reset = tk.Button(left_panel, text="Reiniciar Tablero", command=self.reset_board,
                              bg="#dce6f1", fg="#0a66c2", font=('Arial', 11), cursor="hand2")
        btn_reset.pack(fill=tk.X)

        # Panel derecho (Grid)
        grid_frame = tk.Frame(self.root, bg="white", bd=2, relief=tk.RIDGE)
        grid_frame.pack(side=tk.RIGHT, padx=20, pady=20)

        for r in range(self.FILAS):
            for c in range(self.COLS):
                lbl = tk.Label(grid_frame, text="", width=4, height=2, 
                               font=('Arial', 20, 'bold'), bd=1, relief="solid", bg="white")
                lbl.place(x=c*self.CELL_SIZE, y=r*self.CELL_SIZE, width=self.CELL_SIZE, height=self.CELL_SIZE)
                lbl.bind("<Button-1>", lambda event, row=r, col=c: self.handle_cell_click(row, col))
                self.cell_labels[r][c] = lbl

        grid_frame.config(width=self.COLS*self.CELL_SIZE, height=self.FILAS*self.CELL_SIZE)

    # --- LÓGICA DE EDICIÓN ---
    def handle_cell_click(self, r, c):
        current_val = self.grid_state[r][c]

        if current_val == 0: # Poner número
            num_to_set = self.next_number_to_place
            self.grid_state[r][c] = num_to_set
            self.update_cell_visual(r, c, str(num_to_set), "white", "black")
            self.next_number_to_place += 1

        elif current_val > 0: # Poner muro y renumerar
            deleted_num = current_val
            self.grid_state[r][c] = -1 
            self.update_cell_visual(r, c, "X", "#333333", "white")
            self.renumber_subsequent_pins(deleted_num)

        elif current_val == -1: # Borrar muro
            self.grid_state[r][c] = 0
            self.update_cell_visual(r, c, "", "white", "black")

    def renumber_subsequent_pins(self, deleted_num):
        max_found = 0
        for r in range(self.FILAS):
            for c in range(self.COLS):
                val = self.grid_state[r][c]
                if val > 0:
                    if val > deleted_num:
                        new_val = val - 1
                        self.grid_state[r][c] = new_val
                        self.update_cell_visual(r, c, str(new_val), "white", "black")
                        if new_val > max_found: max_found = new_val
                    elif val > max_found:
                         max_found = val
        self.next_number_to_place = max_found + 1

    def update_cell_visual(self, r, c, text, bg_color, fg_color="black"):
        lbl = self.cell_labels[r][c]
        lbl.config(text=text, bg=bg_color, fg=fg_color)

    def reset_board(self):
        self.grid_state = [[0 for _ in range(self.COLS)] for _ in range(self.FILAS)]
        self.next_number_to_place = 1
        for r in range(self.FILAS):
            for c in range(self.COLS):
                self.update_cell_visual(r, c, "", "white")

    # --- LÓGICA RESOLVER ---
    def iniciar_thread_solver(self):
        # Limpieza visual previa
        for r in range(self.FILAS):
            for c in range(self.COLS):
                val = self.grid_state[r][c]
                if val == 0: self.update_cell_visual(r, c, "", "white")
                elif val > 0: self.update_cell_visual(r, c, str(val), "white", "black")
        
        threading.Thread(target=self.start_solving).start()

    def start_solving(self):
        tablero_trabajo = [fila[:] for fila in self.grid_state]
        checkpoints = []
        total_jugables = 0
        inicio = None

        for r in range(self.FILAS):
            for c in range(self.COLS):
                val = tablero_trabajo[r][c]
                if val != -1: total_jugables += 1
                if val > 0:
                    checkpoints.append(val)
                    if val == 1: inicio = (r, c)
        
        checkpoints.sort()

        if not checkpoints or checkpoints[0] != 1:
            messagebox.showerror("Error", "Falta el número 1.")
            return
        
        # Validar secuencia
        for i in range(len(checkpoints)):
            if checkpoints[i] != i + 1:
                 messagebox.showerror("Error", f"Secuencia incompleta. Falta el {i+1}.")
                 return

        idx_objetivo_inicial = 1
        solucion = self.backtracking_solver(tablero_trabajo, inicio[0], inicio[1], [inicio], total_jugables, checkpoints, idx_objetivo_inicial)

        if solucion:
            self.visualize_gradient_path(solucion)
        else:
            messagebox.showwarning("Ups", "No se encontró solución.")

    def backtracking_solver(self, tablero, r, c, camino, meta_pasos, checkpoints, idx_objetivo):
        if len(camino) == meta_pasos:
            if tablero[r][c] == checkpoints[-1]: return camino
            return None

        valor_objetivo = checkpoints[idx_objetivo] if idx_objetivo < len(checkpoints) else 9999
        movimientos = [(-1, 0), (1, 0), (0, -1), (0, 1)]

        for dr, dc in movimientos:
            nr, nc = r + dr, c + dc
            if 0 <= nr < self.FILAS and 0 <= nc < self.COLS:
                val_vecino = tablero[nr][nc]
                if val_vecino != -1 and (nr, nc) not in camino:
                    nuevo_idx_objetivo = idx_objetivo
                    es_movido_valido = False
                    
                    if val_vecino == 0:
                        es_movido_valido = True
                    elif val_vecino == valor_objetivo:
                        es_movido_valido = True
                        nuevo_idx_objetivo += 1
                    
                    if es_movido_valido:
                        res = self.backtracking_solver(tablero, nr, nc, camino + [(nr, nc)], meta_pasos, checkpoints, nuevo_idx_objetivo)
                        if res: return res
        return None

    # --- GRADIENTE ---
    def visualize_gradient_path(self, camino):
        total_steps = len(camino)
        if total_steps <= 1: return

        # Colores (Rojo suave -> Naranja/Amarillo)
        start_color_hex = "#FF5F6D"
        end_color_hex = "#FFC371"

        for i, (r, c) in enumerate(camino):
            fraction = i / (total_steps - 1)
            color_hex = self._get_gradient_color(start_color_hex, end_color_hex, fraction)
            
            original_val = self.grid_state[r][c]
            text_to_show = str(original_val) if original_val > 0 else ""
            
            self.update_cell_visual(r, c, text_to_show, color_hex, "white")
            self.root.update_idletasks()

    def _get_gradient_color(self, start_hex, end_hex, fraction):
        def hex_to_rgb(h):
            h = h.lstrip('#')
            return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

        def rgb_to_hex(rgb):
            return '#%02x%02x%02x' % tuple(int(c) for c in rgb)

        r1, g1, b1 = hex_to_rgb(start_hex)
        r2, g2, b2 = hex_to_rgb(end_hex)

        r = r1 + (r2 - r1) * fraction
        g = g1 + (g2 - g1) * fraction
        b = b1 + (b2 - b1) * fraction

        return rgb_to_hex((r, g, b))

if __name__ == "__main__":
    root = tk.Tk()
    app = ZipSolverInteractive(root)
    root.mainloop()