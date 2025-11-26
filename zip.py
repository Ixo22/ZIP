import tkinter as tk
from tkinter import messagebox
import threading
import traceback
from collections import deque

class ZipSolverFinal:
    def __init__(self, root):
        self.root = root
        self.root.title("Solver ZIP - V7 (Detección Automática)")
        self.root.configure(bg="#f0f2f5") 

        # Configuración del tablero
        self.FILAS = 7
        self.COLS = 7
        self.CELL_SIZE = 50 

        # --- ESTADO INTERNO ---
        # 0=Vacío, >0=Checkpoint
        self.grid_content = [[0 for _ in range(self.COLS)] for _ in range(self.FILAS)]
        
        # Muros
        self.walls_v = [[False for _ in range(self.COLS)] for _ in range(self.FILAS)]
        self.walls_h = [[False for _ in range(self.COLS)] for _ in range(self.FILAS)]

        # Widgets
        self.widgets_cells = [[None for _ in range(self.COLS)] for _ in range(self.FILAS)]
        self.widgets_walls_v = [[None for _ in range(self.COLS)] for _ in range(self.FILAS)]
        self.widgets_walls_h = [[None for _ in range(self.COLS)] for _ in range(self.FILAS)]

        self.next_number_to_place = 1

        self.crear_interfaz()

    def crear_interfaz(self):
        # PANEL IZQUIERDO
        left_panel = tk.Frame(self.root, bg="#f0f2f5", padx=20, pady=20)
        left_panel.pack(side=tk.LEFT, fill=tk.Y)

        tk.Label(left_panel, text="Instrucciones:", font=("Arial", 12, "bold"), bg="#f0f2f5").pack(anchor="w")
        instr = (
            "1. Clic en CASILLA: Pone número.\n"
            "   (Clic otra vez: Borra el número).\n\n"
            "2. Clic en BORDES: Crea muros.\n"
            "   (Define la forma del nivel usando\n    solo los muros).\n"
        )
        tk.Label(left_panel, text=instr, justify=tk.LEFT, bg="#f0f2f5", pady=10).pack(anchor="w")

        btn_solve = tk.Button(left_panel, text="RESOLVER", command=self.iniciar_calculo, 
                              bg="#0a66c2", fg="white", font=('Arial', 14, 'bold'), cursor="hand2", pady=10)
        btn_solve.pack(fill=tk.X, pady=(20, 10))

        btn_reset = tk.Button(left_panel, text="Borrar Todo", command=self.reset_board,
                              bg="#dce6f1", fg="#0a66c2", font=('Arial', 11), cursor="hand2")
        btn_reset.pack(fill=tk.X)
        
        self.lbl_status = tk.Label(left_panel, text="Listo", fg="grey", bg="#f0f2f5", font=("Arial", 10, "bold"))
        self.lbl_status.pack(side=tk.BOTTOM, pady=20)

        # PANEL DERECHO (GRID)
        grid_frame = tk.Frame(self.root, bg="white", padx=20, pady=20, bd=2, relief=tk.RIDGE)
        grid_frame.pack(side=tk.RIGHT, padx=20, pady=20)

        for r in range(self.FILAS):
            for c in range(self.COLS):
                # CASILLA
                lbl = tk.Label(grid_frame, text="", width=4, height=2, 
                               font=('Arial', 16, 'bold'), bg="#f0f2f5", relief="flat")
                lbl.grid(row=r*2, column=c*2, padx=0, pady=0)
                lbl.bind("<Button-1>", lambda e, row=r, col=c: self.click_cell(row, col))
                self.widgets_cells[r][c] = lbl

                # MURO VERTICAL
                if c < self.COLS - 1:
                    btn_v = tk.Button(grid_frame, bg="#e0e0e0", bd=0, cursor="sb_h_double_arrow", width=1)
                    btn_v.grid(row=r*2, column=c*2+1, sticky="ns", padx=0)
                    btn_v.config(command=lambda row=r, col=c: self.toggle_wall_v(row, col))
                    self.widgets_walls_v[r][c] = btn_v

                # MURO HORIZONTAL
                if r < self.FILAS - 1:
                    btn_h = tk.Button(grid_frame, bg="#e0e0e0", bd=0, cursor="sb_v_double_arrow", height=1)
                    btn_h.grid(row=r*2+1, column=c*2, sticky="ew", pady=0)
                    btn_h.config(command=lambda row=r, col=c: self.toggle_wall_h(row, col))
                    self.widgets_walls_h[r][c] = btn_h
                
                # DECORACIÓN ESQUINA
                if c < self.COLS - 1 and r < self.FILAS - 1:
                    tk.Frame(grid_frame, bg="white", width=4, height=4).grid(row=r*2+1, column=c*2+1)

    # --- INTERACCIÓN ---

    def click_cell(self, r, c):
        # NUEVA SECUENCIA SOLICITADA: Vacío (0) <-> Número (N)
        val = self.grid_content[r][c]
        
        if val == 0: # Poner número
            new_val = self.next_number_to_place
            self.grid_content[r][c] = new_val
            self.widgets_cells[r][c].config(text=str(new_val), bg="white", fg="black")
            self.next_number_to_place += 1
            
        else: # (val > 0) Borrar número y renumerar
            removed = val
            self.grid_content[r][c] = 0
            self.widgets_cells[r][c].config(text="", bg="#f0f2f5", fg="black")
            self.renumber(removed)

    def renumber(self, deleted):
        max_n = 0
        for r in range(self.FILAS):
            for c in range(self.COLS):
                v = self.grid_content[r][c]
                if v > 0:
                    if v > deleted:
                        self.grid_content[r][c] = v - 1
                        self.widgets_cells[r][c].config(text=str(v-1))
                        if (v-1) > max_n: max_n = v-1
                    elif v > max_n:
                        max_n = v
        self.next_number_to_place = max_n + 1

    def toggle_wall_v(self, r, c):
        state = self.walls_v[r][c]
        self.walls_v[r][c] = not state
        color = "black" if not state else "#e0e0e0"
        self.widgets_walls_v[r][c].config(bg=color)

    def toggle_wall_h(self, r, c):
        state = self.walls_h[r][c]
        self.walls_h[r][c] = not state
        color = "black" if not state else "#e0e0e0"
        self.widgets_walls_h[r][c].config(bg=color)

    def reset_board(self):
        self.grid_content = [[0]*self.COLS for _ in range(self.FILAS)]
        self.walls_v = [[False]*self.COLS for _ in range(self.FILAS)]
        self.walls_h = [[False]*self.COLS for _ in range(self.FILAS)]
        self.next_number_to_place = 1
        for r in range(self.FILAS):
            for c in range(self.COLS):
                self.widgets_cells[r][c].config(text="", bg="#f0f2f5")
                if self.widgets_walls_v[r][c]: self.widgets_walls_v[r][c].config(bg="#e0e0e0")
                if self.widgets_walls_h[r][c]: self.widgets_walls_h[r][c].config(bg="#e0e0e0")
        self.lbl_status.config(text="Reiniciado", fg="grey")

    # --- LÓGICA INTELIGENTE ---

    def iniciar_calculo(self):
        # Limpieza visual
        for r in range(self.FILAS):
            for c in range(self.COLS):
                v = self.grid_content[r][c]
                self.widgets_cells[r][c].config(bg="white" if v > 0 else "#f0f2f5")
        
        self.lbl_status.config(text="Calculando área...", fg="blue")
        threading.Thread(target=self.thread_logic, daemon=True).start()

    def thread_logic(self):
        try:
            grid = [fila[:] for fila in self.grid_content]
            wv = [fila[:] for fila in self.walls_v]
            wh = [fila[:] for fila in self.walls_h]
            
            checkpoints = []
            inicio = None
            
            for r in range(self.FILAS):
                for c in range(self.COLS):
                    v = grid[r][c]
                    if v > 0:
                        checkpoints.append(v)
                        if v == 1: inicio = (r, c)
            
            checkpoints.sort()
            
            if not checkpoints or checkpoints[0] != 1:
                self.root.after(0, lambda: messagebox.showerror("Error", "Falta el número 1."))
                return

            # --- MAGIA: CÁLCULO AUTOMÁTICO DE ÁREA JUGABLE (BFS) ---
            # Hacemos una 'inundación' desde el 1 para ver cuántas celdas son accesibles
            # respetando los muros que ha puesto el usuario.
            total_jugables = self.calcular_area_accesible(inicio, wv, wh)
            print(f"DEBUG: Celdas detectadas dentro de los muros: {total_jugables}")

            # Backtracking
            path = self.backtracking(grid, wv, wh, inicio[0], inicio[1], [inicio], total_jugables, checkpoints, 1)

            if path:
                self.root.after(0, lambda: self.animar(path))
            else:
                self.root.after(0, lambda: self.lbl_status.config(text="Sin solución", fg="red"))
                self.root.after(0, lambda: messagebox.showwarning("Falló", "No se encontró camino."))

        except Exception as e:
            traceback.print_exc()

    def calcular_area_accesible(self, inicio, wv, wh):
        """Usa BFS para contar cuántas celdas se pueden alcanzar desde el inicio sin cruzar muros"""
        visitados = set()
        cola = deque([inicio])
        visitados.add(inicio)
        count = 0
        
        while cola:
            r, c = cola.popleft()
            count += 1
            
            moves = [
                (-1, 0, 'h', -1, 0), # Arr
                (1, 0, 'h', 0, 0),   # Abj
                (0, -1, 'v', 0, -1), # Izq
                (0, 1, 'v', 0, 0)    # Der
            ]
            
            for dr, dc, wtype, wr, wc in moves:
                nr, nc = r + dr, c + dc
                if 0 <= nr < self.FILAS and 0 <= nc < self.COLS:
                    if (nr, nc) not in visitados:
                        # Chequeo de Muros
                        blocked = False
                        if wtype == 'h':
                            if wh[r + wr][c + wc]: blocked = True
                        else:
                            if wv[r + wr][c + wc]: blocked = True
                        
                        if not blocked:
                            visitados.add((nr, nc))
                            cola.append((nr, nc))
        return count

    def backtracking(self, grid, wv, wh, r, c, camino, meta, checkpoints, idx_obj):
        if len(camino) == meta:
            if grid[r][c] == checkpoints[-1]: return camino
            return None

        val_meta = checkpoints[idx_obj] if idx_obj < len(checkpoints) else 9999
        moves = [(-1, 0, 'h', -1, 0), (1, 0, 'h', 0, 0), (0, -1, 'v', 0, -1), (0, 1, 'v', 0, 0)]

        for dr, dc, wtype, wr, wc in moves:
            nr, nc = r + dr, c + dc
            if 0 <= nr < self.FILAS and 0 <= nc < self.COLS:
                blocked = False
                if wtype == 'h':
                    if wh[r + wr][c + wc]: blocked = True
                else:
                    if wv[r + wr][c + wc]: blocked = True
                
                if not blocked:
                    val_dest = grid[nr][nc]
                    if (nr, nc) not in camino:
                        can_enter = False
                        new_idx = idx_obj
                        if val_dest == 0: can_enter = True
                        elif val_dest == val_meta:
                            can_enter = True
                            new_idx += 1
                        
                        if can_enter:
                            res = self.backtracking(grid, wv, wh, nr, nc, camino + [(nr, nc)], meta, checkpoints, new_idx)
                            if res: return res
        return None

    def animar(self, path):
        self.lbl_status.config(text="¡RESUELTO!", fg="green")
        c1 = (0, 100, 255)
        c2 = (0, 255, 200)
        total = len(path)
        for i, (r, c) in enumerate(path):
            f = i / (total - 1) if total > 1 else 1
            nr = int(c1[0] + (c2[0]-c1[0])*f)
            ng = int(c1[1] + (c2[1]-c1[1])*f)
            nb = int(c1[2] + (c2[2]-c1[2])*f)
            hex_c = f'#{nr:02x}{ng:02x}{nb:02x}'
            self.root.after(i*30, self.paint_step, r, c, hex_c)

    def paint_step(self, r, c, color):
        v = self.grid_content[r][c]
        txt = str(v) if v > 0 else ""
        self.widgets_cells[r][c].config(bg=color, text=txt, fg="white" if v > 0 else "black")

if __name__ == "__main__":
    root = tk.Tk()
    app = ZipSolverFinal(root)
    root.mainloop()