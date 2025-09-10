import carla
import random
import queue
import numpy as np
import zmq

def main():
    # --- Configuración de ZeroMQ ---
    context = zmq.Context()
    socket = context.socket(zmq.PUB)
    socket.bind("tcp://*:5555")
    print("ZMQ Publisher listo en el puerto 5555")

    client = carla.Client('localhost', 2000)
    client.set_timeout(10.0)
    world = client.get_world()
    
    actor_list = []
    original_settings = world.get_settings()
    
    try:
        # CONFIGURACIÓN DE LA SIMULACIÓN
        settings = world.get_settings()
        settings.synchronous_mode = True
        settings.fixed_delta_seconds = 0.05
        world.apply_settings(settings)
        blueprint_library = world.get_blueprint_library()
        traffic_manager = client.get_trafficmanager(8000)
        traffic_manager.set_synchronous_mode(True)
        spawn_points = world.get_map().get_spawn_points()
        number_of_vehicles = 50
        blueprints = blueprint_library.filter('vehicle.*')
        for i in range(number_of_vehicles):
            blueprint = random.choice(blueprints)
            spawn_point = random.choice(spawn_points)
            vehicle = world.try_spawn_actor(blueprint, spawn_point)
            if vehicle is not None:
                actor_list.append(vehicle)
                vehicle.set_autopilot(True)
        print(f"Generados {len(actor_list)} vehículos.")
        traffic_lights = world.get_actors().filter('traffic.traffic_light*')
        if not traffic_lights:
            print("No se encontraron semáforos.")
            return
        target_traffic_light = traffic_lights[0]
        camera_bp = blueprint_library.find('sensor.camera.rgb')
        camera_bp.set_attribute('image_size_x', '800')
        camera_bp.set_attribute('image_size_y', '600')
        camera_transform = carla.Transform(carla.Location(z=4), carla.Rotation(yaw=90, pitch=-25))
        camera = world.spawn_actor(camera_bp, camera_transform, attach_to=target_traffic_light)
        actor_list.append(camera)
        image_queue = queue.Queue()
        camera.listen(image_queue.put)

        # 4. BUCLE PRINCIPAL MAESTRO
        while True:
            world.tick()
            try:
                image = image_queue.get(block=False)
                
                array = np.frombuffer(image.raw_data, dtype=np.dtype("uint8"))
                array = np.reshape(array, (image.height, image.width, 4))
                
                data_package = {
                    'metadata': {
                        'width': image.width,
                        'height': image.height,
                        'frame': image.frame,
                        'timestamp': image.timestamp # <--- AÑADIR ESTA LÍNEA
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