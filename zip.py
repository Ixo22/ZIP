import tkinter as tk
from tkinter import messagebox
import threading
import time
import traceback

class ZipSolverFinal:
    def __init__(self, root):
        self.root = root
        self.root.title("Solver ZIP - V5 (Thread Safe)")
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
            "1. Clic en Vacío → Pone número.\n"
            "2. Clic en Número → Pone Muro (X).\n"
            "3. Clic en Muro → Borra.\n\n"
            "¡IMPORTANTE!\nMarca con 'X' todo el espacio\nque sobre del tablero."
        )
        tk.Label(left_panel, text=instr_text, font=("Arial", 10), justify=tk.LEFT, bg="#f0f2f5", pady=10).pack(anchor="w")

        btn_solve = tk.Button(left_panel, text="RESOLVER", command=self.iniciar_calculo, 
                              bg="#0a66c2", fg="white", font=('Arial', 14, 'bold'), cursor="hand2", pady=10)
        btn_solve.pack(fill=tk.X, pady=(20, 10))

        btn_reset = tk.Button(left_panel, text="Reiniciar Tablero", command=self.reset_board,
                              bg="#dce6f1", fg="#0a66c2", font=('Arial', 11), cursor="hand2")
        btn_reset.pack(fill=tk.X)
        
        # Etiqueta de estado
        self.lbl_status = tk.Label(left_panel, text="Listo", fg="grey", bg="#f0f2f5", font=("Arial", 9))
        self.lbl_status.pack(side=tk.BOTTOM, pady=10)

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
        self.lbl_status.config(text="Tablero reiniciado", fg="grey")

    # --- HILO SEGURO PARA RESOLVER ---
    def iniciar_calculo(self):
        # Limpiar colores previos
        for r in range(self.FILAS):
            for c in range(self.COLS):
                val = self.grid_state[r][c]
                if val == 0: self.update_cell_visual(r, c, "", "white")
                elif val > 0: self.update_cell_visual(r, c, str(val), "white", "black")
        
        self.lbl_status.config(text="Calculando...", fg="blue")
        # Lanzamos el hilo, pero NO toca la GUI. Solo calcula.
        threading.Thread(target=self.thread_logic, daemon=True).start()

    def thread_logic(self):
        print("DEBUG: Inicio del hilo de cálculo")
        try:
            # 1. Copia de seguridad de los datos (para no leer variables mientras la GUI cambia)
            tablero = [fila[:] for fila in self.grid_state]
            
            # 2. Preparar datos
            checkpoints = []
            total_jugables = 0
            inicio = None

            for r in range(self.FILAS):
                for c in range(self.COLS):
                    val = tablero[r][c]
                    if val != -1: total_jugables += 1
                    if val > 0:
                        checkpoints.append(val)
                        if val == 1: inicio = (r, c)
            
            checkpoints.sort()
            
            # Validaciones (Si fallan, devolvemos un diccionario con error)
            if not checkpoints or checkpoints[0] != 1:
                self.root.after(0, lambda: messagebox.showerror("Error", "Falta el número 1"))
                return

            # 3. Ejecutar Backtracking
            print(f"DEBUG: Buscando camino. Meta pasos: {total_jugables}")
            solucion = self.backtracking(tablero, inicio[0], inicio[1], [inicio], total_jugables, checkpoints, 1)

            # 4. VOLVER AL HILO PRINCIPAL
            if solucion:
                print("DEBUG: Solución encontrada. Enviando a GUI.")
                self.root.after(0, lambda: self.animar_solucion(solucion))
            else:
                print("DEBUG: Fin del cálculo. Sin solución.")
                # Verificamos si hay demasiados espacios vacíos
                msg = "No se encontró solución."
                if total_jugables > len(checkpoints) + 20: # Heurística
                    msg += "\n\nPista: Tienes muchas casillas blancas.\n¿Olvidaste marcar los muros (X)?"
                
                self.root.after(0, lambda: self.mostrar_aviso_fallo(msg))

        except Exception as e:
            err = traceback.format_exc()
            print(err)
            self.root.after(0, lambda: messagebox.showerror("Error Crítico", f"{e}"))

    def mostrar_aviso_fallo(self, msg):
        self.lbl_status.config(text="Sin solución", fg="red")
        messagebox.showwarning("Resultado", msg)

    def backtracking(self, tablero, r, c, camino, meta_pasos, checkpoints, idx_objetivo):
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
                    nuevo_idx = idx_objetivo
                    es_valido = False
                    
                    if val_vecino == 0:
                        es_valido = True
                    elif val_vecino == valor_objetivo:
                        es_valido = True
                        nuevo_idx += 1
                    
                    if es_valido:
                        res = self.backtracking(tablero, nr, nc, camino + [(nr, nc)], meta_pasos, checkpoints, nuevo_idx)
                        if res: return res
        return None

    # --- ANIMACIÓN GRADIENTE (HILO PRINCIPAL) ---
    def animar_solucion(self, camino):
        self.lbl_status.config(text="¡Resuelto!", fg="green")
        total_steps = len(camino)
        
        # Colores: Rojo (#FF5F6D) -> Amarillo (#FFC371)
        # Puedes cambiar estos hex para cambiar el estilo
        c1 = (255, 95, 109) 
        c2 = (255, 195, 113)

        for i, (r, c) in enumerate(camino):
            fraction = i / max(1, total_steps - 1)
            
            # Interpolación lineal manual
            nr = int(c1[0] + (c2[0] - c1[0]) * fraction)
            ng = int(c1[1] + (c2[1] - c1[1]) * fraction)
            nb = int(c1[2] + (c2[2] - c1[2]) * fraction)
            color_hex = f'#{nr:02x}{ng:02x}{nb:02x}'

            original_val = self.grid_state[r][c]
            text = str(original_val) if original_val > 0 else ""
            
            # Usamos after escalonado para la animación
            self.root.after(i * 30, self.update_cell_visual, r, c, text, color_hex, "white")

if __name__ == "__main__":
    root = tk.Tk()
    app = ZipSolverFinal(root)
    root.mainloop()