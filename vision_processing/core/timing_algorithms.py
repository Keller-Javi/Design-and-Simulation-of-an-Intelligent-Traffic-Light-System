
class TimingAlgorithms:
    SEQUENCES = ["A", "B", "C", "D"]

    def __init__(self, algorithm_type="fixed_time"):
        self.algorithm_type = algorithm_type

        self.current_index = 0  # Comienza en NS
        self.current_color = "RED"

        self.yellow_time = 5
        self.red_time = 2

        self.current_green_time = 20
        self.fixed_green_time = 25

        self.min_green_time = 20
        self.max_green_time = 35

        self.last_change_time = 0.0

    def update(self, sem_counts, sim_time):
        """
        Entrada:
            sem_counts = {
                "N": int,
                "S": int,
                "E": int,
                "O": int
            }
            sim_time = tiempo simulado actual (segundos)

        Salida:
            state_dict = {
                "A": "GREEN",
                "B": "RED",
                "C": "RED",
                "D": "RED"
            }
        """

        elapsed = sim_time - self.last_change_time

        # -----------------------------------------
        # 1) Estamos en verde
        # -----------------------------------------
        if self.current_color == "GREEN":
            if elapsed >= self.current_green_time:
                self.current_color = "YELLOW"
                self.last_change_time = sim_time

        # -----------------------------------------
        # 2) Estamos en amarillo
        # -----------------------------------------
        elif self.current_color == "YELLOW":
            if elapsed >= self.yellow_time:
                self.current_color = "RED"
                self.last_change_time = sim_time

        # -----------------------------------------
        # 3) Estamos en rojo
        # -----------------------------------------
        elif self.current_color == "RED":
            if elapsed >= self.red_time:

                # Alternar entre NS y EO
                self.current_index = (self.current_index + 1) % 2

                curr_seq = self.SEQUENCES[self.current_index]

                # Calcular tiempo de verde
                if self.algorithm_type == "actuated_control":
                    self.current_green_time = self.method1(
                        curr_seq, sem_counts
                    )

                elif self.algorithm_type == "fixed_time":
                    self.current_green_time = self.method_fixed()

                elif self.algorithm_type == "max_pressure":
                    self.current_green_time = self.method_pressure(
                        curr_seq, sem_counts
                    )

                else:
                    raise NotImplementedError(
                        f"Algoritmo {self.algorithm_type} no existe"
                    )

                self.current_color = "GREEN"
                self.last_change_time = sim_time

        # -----------------------------------------
        # Construir estado de salida
        # -----------------------------------------
        curr_seq = self.SEQUENCES[self.current_index]

        return {
            "states": self._build_state(
                curr_seq, self.current_color
            )
        }

    # -----------------------------------------
    # Construir estado de los semáforos
    # -----------------------------------------
    def _build_state(self, active_seq, color):
        state_dict = {}

        for seq in self.SEQUENCES:
            if seq == active_seq:
                state_dict[seq] = color
            else:
                state_dict[seq] = "RED"

    # -----------------------------------------
    # ALGORITMO 1: DEMANDA POR FASE
    # -----------------------------------------
    def method1(self, curr_seq, sem_counts):
        """
        Compara la cantidad total de vehículos
        de la fase actual contra la fase opuesta.

        Devuelve min_green_time o max_green_time.
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

    # -----------------------------------------
    # ALGORITMO FIJO
    # -----------------------------------------
    def method_fixed(self):
        """Siempre retorna el tiempo fijo configurado."""
        return self.fixed_green_time

    # -----------------------------------------
    # ALGORITMO PRESSURE
    # -----------------------------------------
    def method_pressure(self, curr_seq, sem_counts):
        """
        Variante simplificada basada en la diferencia
        de demanda entre las dos fases.

        No considera vehículos de salida.
        """

        next_seq = self.SEQUENCES[
            (self.SEQUENCES.index(curr_seq) + 1) % 4
        ]

        pressure = sem_counts[curr_seq] - sem_counts[next_seq]

        min_g = 15
        max_g = 45

        if pressure <= 0:
            return min_g

        p_norm = min(pressure / 4, 1.0)

        green = min_g + p_norm * (max_g - min_g)

        return int(green)
