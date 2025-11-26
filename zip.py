import tkinter as tk
from tkinter import messagebox
import threading
import time

class ZipSolverApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Solver Zip LinkedIn - Lógica Correcta (Checkpoints)")
        
        # AJUSTE: LinkedIn suele usar tableros más grandes. Ponemos 7x7 por defecto.
        self.FILAS = 7
        self.COLS = 7
        
        self.celdas_var = [] 
        self.entries = []    
        self.original_board = [] # Guardamos qué era pista y qué era vacío

        self.crear_interfaz()

    def crear_interfaz(self):
        main_frame = tk.Frame(self.root, padx=10, pady=10)
        main_frame.pack(side=tk.LEFT)

        tk.Label(main_frame, text="1. Pon los Checkpoints (1, 2, 3...)\n2. Pon 'X' en muros.\n3. Deja vacíos (0) los caminos.", font=('Arial', 9)).grid(row=0, column=0, columnspan=self.FILAS)

        for r in range(self.FILAS):
            fila_vars = []
            fila_entries = []
            for c in range(self.COLS):
                var = tk.StringVar()
                var.trace("w", lambda name, index, mode, v=var: self.validar_input(v))
                
                # Fuente más pequeña si el tablero es grande
                entry = tk.Entry(main_frame, textvariable=var, width=3, justify='center', font=('Arial', 14))
                entry.grid(row=r+1, column=c, padx=1, pady=1)
                
                fila_vars.append(var)
                fila_entries.append(entry)
            self.celdas_var.append(fila_vars)
            self.entries.append(fila_entries)

        btn_solve = tk.Button(main_frame, text="RESOLVER", command=self.iniciar_thread, bg="#0a66c2", fg="white", font=('Arial', 12, 'bold'))
        btn_solve.grid(row=self.FILAS+1, column=0, columnspan=self.FILAS, pady=10, sticky="ew")
        
        btn_clear = tk.Button(main_frame, text="Limpiar", command=self.limpiar_tablero)
        btn_clear.grid(row=self.FILAS+2, column=0, columnspan=self.FILAS, sticky="ew")

        # --- LOGS ---
        log_frame = tk.Frame(self.root, padx=10, pady=10)
        log_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        self.log_text = tk.Text(log_frame, width=30, height=20, state='disabled', font=('Consolas', 9))
        self.log_text.pack()

    def log(self, mensaje):
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, "> " + mensaje + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')

    def validar_input(self, var):
        val = var.get()
        if val.lower() == 'x': var.set('X')

    def limpiar_tablero(self):
        for r in range(self.FILAS):
            for c in range(self.COLS):
                self.celdas_var[r][c].set("")
                self.entries[r][c].config(bg="white", fg="black")
        self.log_text.config(state='normal')
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state='disabled')

    def leer_tablero_gui(self):
        tablero = []
        try:
            for r in range(self.FILAS):
                fila = []
                for c in range(self.COLS):
                    val = self.celdas_var[r][c].get().strip().upper()
                    if val == "": fila.append(0)
                    elif val == "X": fila.append(-1)
                    else: fila.append(int(val))
                tablero.append(fila)
            return tablero
        except ValueError:
            messagebox.showerror("Error", "Solo números o 'X'")
            return None

    def iniciar_thread(self):
        threading.Thread(target=self.preparar_resolucion).start()

    def preparar_resolucion(self):
        self.log("Analizando tablero...")
        tablero = self.leer_tablero_gui()
        if tablero is None: return

        # Guardamos una copia para saber qué era original y qué es solución
        self.original_board = [fila[:] for fila in tablero]

        checkpoints = [] # Lista de números fijos [1, 2, 3, 4]
        total_jugables = 0
        inicio = None

        posiciones_pins = {}

        for r in range(self.FILAS):
            for c in range(self.COLS):
                val = tablero[r][c]
                if val != -1: 
                    total_jugables += 1
                if val > 0:
                    checkpoints.append(val)
                    posiciones_pins[val] = (r, c)
                    if val == 1: inicio = (r, c)

        checkpoints.sort()
        
        if not checkpoints or checkpoints[0] != 1:
            self.log("ERROR: Falta el 1.")
            return

        self.log(f"Checkpoints: {checkpoints}")
        self.log(f"Casillas a llenar: {total_jugables}")

        # INICIAR BACKTRACKING
        # Estado: (tablero, r, c, camino, indice_del_siguiente_checkpoint)
        # target_idx = 1 significa que estamos buscando el valor checkpoints[1] (que es el 2)
        
        # El 1 ya está visitado, así que empezamos buscando el siguiente (el 2)
        idx_objetivo_inicial = 1 
        
        t_inicio = time.time()
        solucion = self.backtracking(tablero, inicio[0], inicio[1], [inicio], total_jugables, checkpoints, idx_objetivo_inicial)
        t_fin = time.time()

        if solucion:
            self.log(f"¡SOLUCIÓN! ({round(t_fin - t_inicio, 2)}s)")
            self.pintar_solucion(solucion)
        else:
            self.log("No se encontró solución.")

    def backtracking(self, tablero, r, c, camino, meta_pasos, checkpoints, idx_objetivo):
        """
        r, c: Posición actual
        camino: Lista de tuplas visitadas
        meta_pasos: Cuántas casillas totales hay que cubrir
        checkpoints: Lista [1, 2, 3, 4...]
        idx_objetivo: Índice en 'checkpoints' del número que buscamos ahora.
                      Si buscamos el 2, idx_objetivo es 1.
        """
        
        # 1. HEMOS TERMINADO?
        # Si hemos visitado todas las casillas Y estamos en el último número
        if len(camino) == meta_pasos:
            # Verificar si el último paso es el último checkpoint
            if tablero[r][c] == checkpoints[-1]:
                return camino
            return None # Llenamos el tablero pero no acabamos en el final correcto

        # Valor que estamos buscando ahora mismo (ej: 2)
        # Si ya hemos encontrado el último (ej: 4), ya no buscamos nada, solo llenar huecos vacios hasta acabar
        valor_objetivo = checkpoints[idx_objetivo] if idx_objetivo < len(checkpoints) else 9999

        movimientos = [(-1, 0), (1, 0), (0, -1), (0, 1)]

        for dr, dc in movimientos:
            nr, nc = r + dr, c + dc

            # Validar límites
            if 0 <= nr < self.FILAS and 0 <= nc < self.COLS:
                val_vecino = tablero[nr][nc]
                
                # Si no es muro y no está visitado
                if val_vecino != -1 and (nr, nc) not in camino:
                    
                    nuevo_idx_objetivo = idx_objetivo
                    es_movimiento_valido = False

                    # CASO A: Es una casilla vacía (0)
                    if val_vecino == 0:
                        es_movimiento_valido = True
                    
                    # CASO B: Es un número (Checkpoint)
                    elif val_vecino > 0:
                        # Solo podemos entrar si es EXACTAMENTE el objetivo actual
                        if val_vecino == valor_objetivo:
                            es_movimiento_valido = True
                            nuevo_idx_objetivo += 1 # ¡Lo encontramos! Ahora buscamos el siguiente
                        else:
                            # Es un número, pero no el que toca (ej: encontramos el 4 buscando el 2) -> Prohibido
                            es_movimiento_valido = False 

                    if es_movimiento_valido:
                        res = self.backtracking(tablero, nr, nc, camino + [(nr, nc)], meta_pasos, checkpoints, nuevo_idx_objetivo)
                        if res: return res

        return None

    def pintar_solucion(self, camino):
        # camino es la lista ordenada de pasos [(0,0), (0,1), (0,2)...]
        for paso_num, (r, c) in enumerate(camino):
            val_paso = paso_num + 1 # Paso 1, Paso 2...
            
            # Si era una casilla vacía originalmente, mostramos el número de paso
            if self.original_board[r][c] == 0:
                self.celdas_var[r][c].set(str(val_paso))
                self.entries[r][c].config(fg="blue", bg="#d1e7dd") # Azul para los pasos calculados
            else:
                # Si era un Checkpoint original, lo dejamos en negro/negrita pero cambiamos fondo
                self.entries[r][c].config(bg="#a3cfbb", font=('Arial', 14, 'bold'))

if __name__ == "__main__":
    root = tk.Tk()
    app = ZipSolverApp(root)
    root.mainloop()