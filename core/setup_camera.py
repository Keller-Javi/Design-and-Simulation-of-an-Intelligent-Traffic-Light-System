import queue
import carla

def add_camera_to_traffic_light(world, blueprint_library, target_location):
    all_traffic_lights = world.get_actors().filter('*.traffic_light')
    target_traffic_light = None
        
    min_distance = float('inf')
    for light in all_traffic_lights:
        distance = light.get_location().distance(target_location)
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

    image_queue = queue.Queue()
    camera.listen(image_queue.put)

    return camera, image_queue