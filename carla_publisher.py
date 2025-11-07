
import carla
import queue
import numpy as np

from core.spawn_utils import spawn_vehicles, spawn_pedestrians, delete_vehicles
from core.zmq_publisher import ZMQPublisher
from core.setup_world import SetupWorld

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
        world.apply_settings(settings)

        blueprint_library = world.get_blueprint_library()

        # --- GENERAR TRÁFICO ---
        traffic_manager = client.get_trafficmanager(8000)
        traffic_manager.set_synchronous_mode(True)

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
        blueprints = blueprint_library.filter('vehicle.*')
        
        actor_list = spawn_vehicles(world, blueprints, nearby_spawns, number_of_vehicles, actor_list)

        nearby_spawns = [
            sp for sp in spawn_points 
            if sp.location.distance(target_location_1) > 45.0
            and sp.location.distance(target_location_1) < 90.0
        ]

        # Generate pedestrians
        number_of_pedestrians = 50
        actor_list = spawn_pedestrians(world, client, number_of_pedestrians, actor_list)

        # --- 2. SELECCIONAR UN SEMÁFORO ESPECÍFICO POR UBICACIÓN --- TODO: POSIBLEMNETE NO ES NECESARIO ESTO
        all_traffic_lights = world.get_actors().filter('*.traffic_light')
        target_traffic_light = None
        
        min_distance = float('inf')
        for light in all_traffic_lights:
            distance = light.get_location().distance(target_location_1)
            if distance < min_distance:
                min_distance = distance
                target_traffic_light = light
        
        if not target_traffic_light:
            print("Error: No se pudo encontrar un semáforo cerca de la ubicación objetivo.")
            return
        
        print(f"Semáforo específico seleccionado: ID {target_traffic_light.id} en {target_traffic_light.get_location()}")

        # --- 3. CONFIGURAR LA CÁMARA DEL SEMÁFORO ---
        camera_bp = blueprint_library.find('sensor.camera.rgb')
        camera_bp.set_attribute('image_size_x', '800')
        camera_bp.set_attribute('image_size_y', '600')
        
        camera_transform = carla.Transform(carla.Location(x=-4,z=4.5), carla.Rotation(pitch=-18.22, yaw=90.85, roll=0.00))
        camera = world.spawn_actor(camera_bp, camera_transform, attach_to=target_traffic_light)
        actor_list.append(camera)

        image_queue = queue.Queue()
        camera.listen(image_queue.put)

        # --- 4. BUCLE PRINCIPAL MAESTRO ---
        while True:
            world.tick()

            # Eliminar vehículos lejanos al semáforo
            actor_list = delete_vehicles(actor_list, target_location_1)
            # Generar nuevos vehículos si es necesario
            actor_list = spawn_vehicles(world, blueprints, nearby_spawns, number_of_vehicles, actor_list)
            
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
        world.apply_settings(original_settings)
        client.apply_batch([carla.command.DestroyActor(x) for x in actor_list])
        zmq_publisher.close()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\nCancelado por el usuario.')