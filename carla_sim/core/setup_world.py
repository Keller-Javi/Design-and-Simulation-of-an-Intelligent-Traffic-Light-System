import time
import carla
import math

class SetupWorld(object):
    def __init__(self, client, map_name='Town04'):
        self.client = client
        self.world = client.get_world()
        self.map_name = map_name
    
    def load_map(self):
        if not self.world.get_map().name.endswith(self.map_name):
            print(f"Mundo actual no es {self.map_name}. Cargando {self.map_name}...")
            self.world = self.client.load_world(self.map_name)
            time.sleep(2)
        else:
            print(f"El mundo ya es {self.map_name}.")
        return self.world
    
    def toggle_far_environment_objects(world, center, radius, visible_inside=True, debug=False):
        """
        Activa o desactiva los objetos del entorno según su distancia al punto dado.

        Args:
            world (carla.World): Mundo de CARLA.
            center (carla.Location): Punto central de la ROI.
            radius (float): Radio en metros.
            visible_inside (bool): Si True, mantiene visibles los objetos dentro del radio y oculta los de afuera.
            debug (bool): Si True, muestra info por consola.
        """
        # Lista de etiquetas que queremos controlar
        object_labels = [
            carla.CityObjectLabel.Buildings,
            carla.CityObjectLabel.Fences,
            carla.CityObjectLabel.Poles,
            carla.CityObjectLabel.TrafficSigns,
            carla.CityObjectLabel.Walls,
            carla.CityObjectLabel.Vegetation,
            carla.CityObjectLabel.Static
        ]

        objects_to_toggle = set()

        for label in object_labels:
            env_objs = world.get_environment_objects(label)

            for obj in env_objs:
                obj_location = obj.bounding_box.location  # centro del objeto
                distance = math.sqrt(
                    (obj_location.x - center.x)**2 +
                    (obj_location.y - center.y)**2 +
                    (obj_location.z - center.z)**2
                )

                # Si está fuera del radio, marcamos para ocultar
                if visible_inside and distance > radius:
                    objects_to_toggle.add(obj.id)
                # O al revés, si querés ocultar los de adentro:
                elif not visible_inside and distance <= radius:
                    objects_to_toggle.add(obj.id)

        # Aplicamos el cambio
        world.enable_environment_objects(objects_to_toggle, False)

        if debug:
            print(f"Objetos desactivados: {len(objects_to_toggle)}")
            if len(objects_to_toggle) > 0:
                print("Ejemplo IDs:", list(objects_to_toggle)[:10])

        return objects_to_toggle