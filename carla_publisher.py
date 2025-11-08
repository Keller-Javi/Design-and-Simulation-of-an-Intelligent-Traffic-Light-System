
import carla
import queue
import numpy as np
import sys

from core.spawn_utils import spawn_vehicles, spawn_pedestrians, delete_vehicles
from core.zmq_publisher import ZMQPublisher
from core.setup_world import SetupWorld
from core.setup_camera import add_camera_to_traffic_light
from core.dynamic_weather import Weather

def main():
    # --- Configuración de ZeroMQ ---
    zmq_publisher = ZMQPublisher()

    # --- Conexión a CARLA ---
    client = carla.Client('localhost', 2000)
    client.set_timeout(20.0)

    setup = SetupWorld(client, map_name='Town04')
    
    world = setup.load_map()

    actor_list = []
    original_settings = world.get_settings()
    
    try:
        # --- CONFIGURAR EL MUNDO EN MODO SÍNCRONO ---
        settings = world.get_settings()
        settings.synchronous_mode = True
        settings.fixed_delta_seconds = 0.05
        settings.max_substep_delta_time = 0.05     # Asegura estabilidad del paso de física
        settings.max_substeps = 1
        world.apply_settings(settings)

        blueprint_library = world.get_blueprint_library()

        # --- CONFIGURAR EL CLIMA DINÁMICO ---
        weather = Weather(world.get_weather())
        speed_factor = 1.0
        update_freq = 0.1 / speed_factor

        elapsed_time = 0.0

        # --- GENERAR TRÁFICO ---
        traffic_manager = client.get_trafficmanager(8000)
        traffic_manager.set_synchronous_mode(True)
        #traffic_manager.set_hybrid_physics_mode(True)

        # Limitar la zana de spawn de vehículos
        spawn_points = world.get_map().get_spawn_points()
        
        target_location_1 = carla.Location(x=351, y=-180, z=0.00)
        #target_location_2 = carla.Location(x=351, y=-180, z=0.00)

        nearby_spawns = [
            sp for sp in spawn_points 
            if sp.location.distance(target_location_1) < 80.0
        ]

        # Generate vehicles
        number_of_vehicles = 50

        # No queremos que ciertos vehículos aparezcan
        vehicles_to_not_spawn = ["vehicle.micro.microlino", "vehicle.tesla.cybertruck", "vehicle.bh.crossbike", "vehicle.diamondback.century", "vehicle.gazelle.omafiets"]
        blueprints = blueprint_library.filter('vehicle.*')
        blueprints = [bp for bp in blueprints if bp.id not in vehicles_to_not_spawn]
        
        actor_list = spawn_vehicles(world, blueprints, nearby_spawns, number_of_vehicles, actor_list)

        nearby_spawns = [
            sp for sp in spawn_points 
            if sp.location.distance(target_location_1) > 40.0
            and sp.location.distance(target_location_1) < 80.0
        ]

        # Generate pedestrians
        number_of_pedestrians = 75

        actor_list = spawn_pedestrians(world, client, number_of_pedestrians, actor_list)

        # --- 2. SELECCIONAR UN SEMÁFORO ESPECÍFICO POR UBICACIÓN

        camera, image_queue = add_camera_to_traffic_light(world, blueprint_library, target_location_1)
        actor_list.append(camera)

        # --- 4. BUCLE PRINCIPAL MAESTRO ---
        while True:
            world.tick()

            # --- Actualizar clima dinámico ---
            world_snapshot = world.get_snapshot()
            timestamp = world_snapshot.timestamp
            elapsed_time += timestamp.delta_seconds
            if elapsed_time > update_freq:
                weather.tick(speed_factor * elapsed_time)
                world.set_weather(weather.weather)
                sys.stdout.write('\r' + str(weather) + 12 * ' ')
                sys.stdout.flush()
                elapsed_time = 0.0

            # --- Determinar hora simulada y tránsito dinámico ---
            current_hour = weather.current_hour()
            
            # Determinar cantidad de vehículos según hora
            if 7 <= current_hour < 9 or 11 <= current_hour < 13 or 16 <= current_hour < 18:
                number_of_vehicles = 50  # Tránsito alto
            elif 6 <= current_hour < 22:
                number_of_vehicles = 25  # Tránsito moderado
            else:
                number_of_vehicles = 10  # Tránsito bajo
            
            # --- Gestionar vehículos dinámicamente ---
            # Eliminar vehículos lejanos al semáforo
            actor_list = delete_vehicles(actor_list, target_location_1)
            # Generar nuevos vehículos si es necesario
            actor_list = spawn_vehicles(world, blueprints, nearby_spawns, number_of_vehicles, actor_list)
            
            # --- PUBLICAR DATOS A TRAVÉS DE ZEROMQ ---
            # Enviar imagen de la cámara
            try:
                image = image_queue.get(block=False)
                array = np.frombuffer(image.raw_data, dtype=np.dtype("uint8"))
                array = np.reshape(array, (image.height, image.width, 4))
                
                zmq_publisher.send_image(image, array)

            except queue.Empty:
                continue

    finally:
        print("\nLimpiando y restaurando la configuración...")

        if 'world' in locals() and 'original_settings' in locals():
            world.apply_settings(original_settings)
        if 'client' in locals() and 'actor_list' in locals():
            actors_to_destroy = [x for x in actor_list if x and x.is_alive]
            client.apply_batch([carla.command.DestroyActor(x) for x in actors_to_destroy])
        
        zmq_publisher.close()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\nCancelado por el usuario.')