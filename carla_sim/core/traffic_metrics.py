import carla
import math
import csv
import os

class TrafficMetrics:
    def __init__(self, world, roi, roi_radius=50.0, draw_roi=True, csv_path="traffic_metrics.csv"):
        # Variables de entorno
        self._world = world
        self._point = roi # Punto que define un radio de interés para la ROI (Region Of Interest)
        self._roi_radius = roi_radius # Radio en metros de la ROI
        self._draw_roi = draw_roi # Si se quiere dibujar la ROI en el mundo de CARLA 
        self.csv_path = csv_path
        
        # Estado previo de vehículos dentro de la ROI
        self.prev_inside = set()
        self.prev_stopped = set()
        if self._draw_roi:
            self.get_roi()

        # Variables para almacenar métricas
        self.vehicle_flow = 0 # Numeros de vehículos que entran o salen del ROI por hora
        self.t_waiting_vehicles = 0 # Tiempo total de espera de vehículos en semáforos dentro del ROI
        self.avg_speed = 0.0 # Velocidad promedio de vehículos dentro del ROI
        self.n_stopped_vehicles = 0 # Número de vehículos detenidos en semáforos dentro del ROI
        
        self.accum_speed = 0
        self.count_speed = 0

        # Control del tiempo simulado
        self.last_save_time = 0.0
        self.last_hour = None

        # Crear CSV si no existe
        if not os.path.exists(self.csv_path):
            with open(self.csv_path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["vehicle_flow", "avg_speed", "stopped_vehicles", "waiting_time"])

    def is_inside_roi(self, loc):
        """Retorna True si el vehículo está dentro del círculo ROI."""
        dx = loc.x - self._point.x
        dy = loc.y - self._point.y
        return dx*dx + dy*dy <= self._roi_radius * self._roi_radius

    def save_to_csv(self):
        """Guarda una fila en el CSV."""
        print(f"Guardando métricas de tráfico.")
        avg_speed = self.accum_speed / self.count_speed if self.count_speed > 0 else 0.0

        with open(self.csv_path, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                self.vehicle_flow,
                avg_speed,
                self.n_stopped_vehicles,
                self.t_waiting_vehicles
            ])

        # Reiniciar métricas
        self.vehicle_flow = 0
        self.t_waiting_vehicles = 0
        self.n_stopped_vehicles = 0
        self.accum_speed = 0
        self.count_speed = 0

    def update(self, current_hour):
        """Se llama cada tick. Obtiene las métricas del tráfico."""
        world_snapshot = self._world.get_snapshot()

        # Guardar métricas cada hora simulada
        if current_hour >= self.last_save_time + 1.0:
            self.save_to_csv()
            self.last_save_time = current_hour
        elif current_hour < 1.0 and self.last_save_time >= 23.0:
            self.save_to_csv()
            self.last_save_time = current_hour

        # Obtener vehículos
        vehicles = self._world.get_actors().filter("vehicle.*")
        current_inside = set()

        for v in vehicles:
            loc = v.get_location()
            inside = self.is_inside_roi(loc)

            if inside:
                current_inside.add(v.id)

                # Velocidad
                vel = v.get_velocity()
                speed = math.sqrt(vel.x**2 + vel.y**2 + vel.z**2)
                self.accum_speed += speed
                self.count_speed += 1

                # Vehículos detenidos
                if speed < 0.1:
                    if not v.id in self.prev_stopped:
                        self.n_stopped_vehicles += 1 # Nuevo vehículo detenido
                        self.prev_stopped.add(v.id)
                    self.t_waiting_vehicles += world_snapshot.timestamp.delta_seconds # Incrementar tiempo de espera
                else:
                    if v.id in self.prev_stopped:
                        self.prev_stopped.remove(v.id)

        # Detectar salidas
        exited  = self.prev_inside - current_inside
        #entered = current_inside - self.prev_inside

        self.vehicle_flow += len(exited)

        # Actualizar estado previo
        self.prev_inside = current_inside

    def get_roi(self):
        """
        Define una ROI circular centrada en self._point con radio self._roi_radius.
        Si draw_roi=True, dibuja la circunferencia en el mundo de CARLA.
        Retorna una tupla (centro, radio).
        """
        center = self._point
        radius = self._roi_radius

        # Dibujar círculo en el plano XY con líneas cada 10 grados aprox
        segments = 36  # mayor número = círculo más suave
        color = carla.Color(255, 0, 0)  # rojo
        life_time = 240.2  # 4 minutos  visible

        for i in range(segments):
                angle1 = (2 * math.pi / segments) * i
                angle2 = (2 * math.pi / segments) * (i + 1)
                x1 = center.x + radius * math.cos(angle1)
                y1 = center.y + radius * math.sin(angle1)
                x2 = center.x + radius * math.cos(angle2)
                y2 = center.y + radius * math.sin(angle2)

                p1 = carla.Location(x=x1, y=y1, z=center.z + 0.5)
                p2 = carla.Location(x=x2, y=y2, z=center.z + 0.5)

                self._world.debug.draw_line(p1, p2, thickness=0.1, color=color, life_time=life_time)

        # También podés marcar el centro:
        self._world.debug.draw_point(center, size=0.2, color=carla.Color(0, 255, 0), life_time=life_time)