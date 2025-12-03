import time

class TimingAlgorithms:
    SEQUENCES = ["A", "B", "C", "D"]
    
    def __init__(self, algorithm_type="method1"):
        self.algorithm_type = algorithm_type

        self.current_index = 0   # Comienza en "A"
        self.current_color = "GREEN"   # Fase inicial
        self.yellow_time = 5
        self.red_time = 2

        self.current_green_time = 20
        self.fixed_green_time = 25     # Tiempo fijo para el método fijo

        self.min_green_time = 20
        self.max_green_time = 35
        self.last_change_time = time.time()

    def update(self, sem_counts):
        """
        Entrada:
            sem_counts = {"A": int, "B": int, "C": int, "D": int} 
        Salida:
            state_dict = { "A": "GREEN", "B": "RED", "C": "RED", "D": "RED" }
        """

        now = time.time()
        elapsed = now - self.last_change_time

        # -------------------------------------------------
        # 1) Estamos en verde
        # -------------------------------------------------
        if self.current_color == "GREEN":
            if elapsed >= self.current_green_time:
                self.current_color = "YELLOW"
                self.last_change_time = now

        # -------------------------------------------------
        # 2) Estamos en amarillo
        # -------------------------------------------------
        elif self.current_color == "YELLOW":
            if elapsed >= self.yellow_time:
                self.current_color = "RED"
                self.last_change_time = now

        # -------------------------------------------------
        # 3) Estamos en rojo
        # -------------------------------------------------
        elif self.current_color == "RED":
            if elapsed >= self.red_time:
                # Cambiar a la siguiente secuencia
                self.current_index = (self.current_index + 1) % 4

                curr_seq = self.SEQUENCES[self.current_index]

                # Calcular tiempo de verde según el algoritmo
                if self.algorithm_type == "method1":
                    self.current_green_time = self.method1(curr_seq, sem_counts)
                elif self.algorithm_type == "fixed":
                    self.current_green_time = self.method_fixed()
                else:
                    raise NotImplementedError(f"Algoritmo {self.algorithm_type} no existe")

                self.current_color = "GREEN"
                self.last_change_time = now

        # -------------------------------------------------
        # Construir el estado a devolver
        # -------------------------------------------------
        curr_seq = self.SEQUENCES[self.current_index]
        return {"states": self._build_state(curr_seq, self.current_color)}

    # -----------------------------------------------------
    # Construir el estado dict
    # -----------------------------------------------------
    def _build_state(self, active_seq, color):
        state_dict = {}

        for seq in self.SEQUENCES:
            if seq == active_seq:
                state_dict[seq] = color
            else:
                # Todo semáforo que no está activo está rojo
                state_dict[seq] = "RED"

        return state_dict

    # -----------------------------------------
    #               ALGORITMO 1
    # -----------------------------------------
    def method1(self, curr_seq, sem_counts):
        """
        Devuelve SIEMPRE 20s o 30s de verde, según la comparación correspondiente.
        """
        if curr_seq == "D":
            decision = sem_counts["D"] > sem_counts["A"]
        elif curr_seq == "A":
            decision = sem_counts["A"] > sem_counts["B"]
        elif curr_seq == "B":
            decision = sem_counts["B"] > sem_counts["C"]
        elif curr_seq == "C":
            decision = sem_counts["C"] > sem_counts["D"]

        return self.max_green_time if decision else self.min_green_time

    # -----------------------------------------------------
    #               ALGORITMO FIJO
    # -----------------------------------------------------
    def method_fixed(self):
        """
        Siempre retorna el tiempo fijo configurado.
        """
        return self.fixed_green_time