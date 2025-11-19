import carla
import random

def spawn_vehicles(world, blueprint_library, spawn_points, number_of_vehicles, actor_list, min_spawn_distance=10.0):
    """
    Descripción: Genera vehículos en el mundo hasta alcanzar el número especificado.
    Returna:
        actor_list (list): Lista de actores (vehículos) en el mundo.
    """
    vehicles_in_world = [
        actor for actor in actor_list 
        if actor and actor.is_alive and 'vehicle.' in actor.type_id
    ]
    
    if len(vehicles_in_world) >= number_of_vehicles:
        return actor_list

    # Obtenemos las ubicaciones de todos los vehículos actuales para las comprobaciones de distancia
    vehicle_locations = [v.get_location() for v in vehicles_in_world]

    # Mezclamos los puntos de spawn para no probar siempre los mismos
    random.shuffle(spawn_points)
    
    # Contamos cuántos vehículos necesitamos generar
    vehicles_to_spawn = number_of_vehicles - len(vehicles_in_world)
    
    spawn_count = 0
    for spawn_point in spawn_points:
        if spawn_count >= vehicles_to_spawn:
            break

        is_safe = True
        # Comprobar si el punto de spawn está demasiado cerca de otro vehículo ya existente
        for loc in vehicle_locations:
            if loc.distance(spawn_point.location) < min_spawn_distance:
                is_safe = False
                break
        
        if is_safe:
            blueprint = random.choice(blueprint_library)
            vehicle = world.try_spawn_actor(blueprint, spawn_point)
            if vehicle is not None:
                actor_list.append(vehicle)
                vehicle.set_autopilot(True)
                vehicle_locations.append(spawn_point.location)
                spawn_count += 1

    return actor_list

def delete_vehicles(actor_list, target_location):
    """
    Descripción: Elimina vehículos que estén a más de 150 metros de la ubicación objetivo.
    Returna:
        actor_list (list): Lista de actores (vehículos) en el mundo.
    """
    vehicles_to_delete = [
        actor for actor in actor_list 
        if actor and actor.is_alive and 'vehicle.' in actor.type_id 
        and target_location.distance(actor.get_location()) > 150.0
    ]

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