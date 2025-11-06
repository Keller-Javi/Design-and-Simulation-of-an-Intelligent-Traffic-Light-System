
import carla
import random
import queue
import numpy as np
import zmq
import time

# Funciones auxiliares
def spawn_vehicles(world, blueprint_library, spawn_points, number_of_vehicles, actor_list):
    """
    Descripción: Genera vehículos en el mundo hasta alcanzar el número especificado.
    Returna:
        actor_list (list): Lista de actores (vehículos) en el mundo.
    """
    vehicles = [actor for actor in actor_list if actor and 'vehicle.' in actor.type_id]

    len_actor_list = vehicles.__len__()

    if len_actor_list > number_of_vehicles: # Si no hace falta generar, se sale 
        return

    for _ in range(number_of_vehicles - len_actor_list): # Generar hasta llegar a number_of_vehicles
            blueprint = random.choice(blueprint_library)
            spawn_point = random.choice(spawn_points)
            vehicle = world.try_spawn_actor(blueprint, spawn_point)
            if vehicle is not None:
                actor_list.append(vehicle)
                vehicle.set_autopilot(True)

    return actor_list

def delete_vehicles(actor_list, target_location):
    """
    Descripción: Elimina vehículos que estén a más de 150 metros de la ubicación objetivo.
    Returna:
        actor_list (list): Lista de actores (vehículos) en el mundo.
    """
    vehicles_to_delete = [actor for actor in actor_list if actor and 'vehicle.' in actor.type_id and target_location.distance(actor.get_location()) > 150.0]

    for actor in actor_list:
        if actor in vehicles_to_delete:
            try:
                actor_list.remove(actor)
                actor.destroy()
            except ValueError:
                pass

    return actor_list

def spawn_pedestrians(world, client, number_of_pedestrians, actor_list):
    """
    Genera peatones en ubicaciones aleatorias y les asigna un controlador de IA.
    """
    print("Generando peatones...")
    pedestrian_list = [actor for actor in actor_list if actor and 'walker.pedestrian.' in actor.type_id]
    if len(pedestrian_list) >= number_of_pedestrians:
        return actor_list

    # 1. Obtener los blueprints de los peatones y del controlador
    walker_blueprints = world.get_blueprint_library().filter('walker.pedestrian.*')
    controller_blueprint = world.get_blueprint_library().find('controller.ai.walker')

    spawn_points = []
    for _ in range(number_of_pedestrians - len(pedestrian_list)):
        spawn_point = carla.Transform()
        # Obtenemos una ubicación aleatoria en una acera
        location = world.get_random_location_from_navigation()
        if location is not None:
            spawn_point.location = location
            spawn_points.append(spawn_point)

    # 2. Generar los peatones en un batch
    batch = []
    for spawn_point in spawn_points:
        walker_bp = random.choice(walker_blueprints)
        if walker_bp.has_attribute('is_invincible'):
            walker_bp.set_attribute('is_invincible', 'false')
        batch.append(carla.command.SpawnActor(walker_bp, spawn_point))

    responses = client.apply_batch_sync(batch, True)
    
    # 3. Asignar un controlador a cada peatón generado
    batch = []
    for response in responses:
        if not response.error:
            walker_actor = world.get_actor(response.actor_id)
            # Guardamos el peatón y su futuro controlador
            pedestrian_list.append({'walker': walker_actor, 'controller': None})
            actor_list.append(walker_actor)
            # Creamos el comando para generar el controlador
            batch.append(carla.command.SpawnActor(controller_blueprint, carla.Transform(), walker_actor))

    responses = client.apply_batch_sync(batch, True)
    
    # 4. Iniciar los controladores
    for i, response in enumerate(responses):
        if not response.error:
            controller_actor = world.get_actor(response.actor_id)
            # Asociamos el controlador con su peatón en nuestra lista
            pedestrian_list[-(i+1)]['controller'] = controller_actor
            actor_list.append(controller_actor)
            
            # Iniciamos el controlador
            controller_actor.start()
            controller_actor.go_to_location(world.get_random_location_from_navigation())
            controller_actor.set_max_speed(1 + random.random()) # Velocidad entre 1 y 2 m/s

    print(f"Generados {len(pedestrian_list)} peatones en total.")
    return actor_list

def main():
    # --- Configuración de ZeroMQ ---
    context = zmq.Context()
    socket = context.socket(zmq.PUB)
    socket.bind("tcp://*:5555")
    print("ZMQ Publisher listo en el puerto 5555")

    client = carla.Client('localhost', 2000)
    client.set_timeout(20.0)
    
    # --- 1. CARGAR EL MUNDO (Town04) ---
    world = client.get_world()
    map_name = 'Town04'
    if not world.get_map().name.endswith(map_name):
        print(f"Mundo actual no es {map_name}. Cargando {map_name}...")
        world = client.load_world(map_name)
        # Esperar un poco para que el mapa se cargue completamente
        time.sleep(2)
    else:
        print(f"El mundo ya es {map_name}.")

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

        nearby_spawns = [sp for sp in spawn_points if sp.location.distance(target_location_1) < 100.0]

        # Generate vehicles
        number_of_vehicles = 50
        blueprints = blueprint_library.filter('vehicle.*')
        
        actor_list = spawn_vehicles(world, blueprints, nearby_spawns, number_of_vehicles, actor_list)

        # Generate pedestrians
        number_of_pedestrians = 30
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
                data_package = {
                    'metadata': {
                        'width': image.width,
                        'height': image.height,
                        'frame': image.frame,
                        'timestamp': image.timestamp
                    },
                    'image': array
                }
                socket.send_pyobj(data_package)

            except queue.Empty:
                continue

    finally:
        print("\nLimpiando y restaurando la configuración...")
        world.apply_settings(original_settings)
        client.apply_batch([carla.command.DestroyActor(x) for x in actor_list])
        socket.close()
        context.term()
        print("Limpieza completa.")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\nCancelado por el usuario.')