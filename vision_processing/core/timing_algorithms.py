
class TimingAlgorithms:
    SEQUENCES = ["A", "B", "C", "D"]
    
    # Esta clase va a alojar los algotirmos de temporización utilizandos
    def __init__(self, algorithm_type="method1"):
        """Al iniciar la clase se puede elegir que algoritmo utilizar"""
        self.algorithm_type = algorithm_type
        self.current_index = 0   # inicia en secuencia A
        self.yellow_time = 10
        self.red_time = 3

    def update(self, sem_counts):
        """
        sem_counts = {"A": int, "B": int, "C": int, "D": int}
        Retorna las acciones de temporización para el simulador.
        """
        curr_seq = self.SEQUENCES[self.current_index]

        # Ejecutar algoritmo seleccionado
        if self.algorithm_type == "method1":
            green = self.method1(curr_seq, sem_counts)
        else:
            raise NotImplementedError("Algoritmo no implementado")

        # Calcular siguiente secuencia
        next_index = (self.current_index + 1) % 4
        next_seq = self.SEQUENCES[next_index]

        # Actualizar estado interno
        self.current_index = next_index

        # Retornar instrucciones
        return {
            "current_sequence": curr_seq,
            "yellow_time": self.yellow_time_time,
            "green_time": green,
            "red_time": self.red_time,
            "next_sequence": next_seq
        }

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

        return 30 if decision else 20