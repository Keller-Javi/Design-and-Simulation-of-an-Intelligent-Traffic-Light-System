import time

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