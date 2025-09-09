import carla
import cv2
import numpy as np
import queue
import random
import time

def main():
    client = carla.Client('localhost', 2000)
    client.set_timeout(10.0)
    world = client.get_world()
    
    # Lista para guardar los actores que creemos y destruirlos al final
    actor_list = []
    
    original_settings = world.get_settings()
    
    try:
        # 1. CONFIGURAR EL MUNDO EN MODO SÍNCRONO (Como ya lo tenías)
        settings = world.get_settings()
        settings.synchronous_mode = True
        settings.fixed_delta_seconds = 0.05 # Simular a 20 FPS
        world.apply_settings(settings)

        blueprint_library = world.get_blueprint_library()

        # 2. GENERAR TRÁFICO (Lógica de generate_traffic.py)
        traffic_manager = client.get_trafficmanager(8000)
        traffic_manager.set_synchronous_mode(True) # MUY IMPORTANTE: Sincronizar el TM
        
        spawn_points = world.get_map().get_spawn_points()
        number_of_vehicles = 50 # Elige cuántos vehículos quieres
        
        blueprints = blueprint_library.filter('vehicle.*')
        
        for i in range(number_of_vehicles):
            blueprint = random.choice(blueprints)
            spawn_point = random.choice(spawn_points)
            vehicle = world.try_spawn_actor(blueprint, spawn_point)
            if vehicle is not None:
                actor_list.append(vehicle)
                vehicle.set_autopilot(True)
        
        print(f"Generados {len(actor_list)} vehículos.")

        # 3. CONFIGURAR LA CÁMARA DEL SEMÁFORO (Como ya lo tenías)
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
        actor_list.append(camera) # Añadir la cámara a la lista para limpiarla después

        image_queue = queue.Queue()
        camera.listen(image_queue.put)

        # 4. BUCLE PRINCIPAL MAESTRO
        while True:
            # Avanzar la simulación un paso. Esto hace avanzar TODO:
            # el mundo, los vehículos del TM, los sensores, etc.
            world.tick()

            try:
                image = image_queue.get(block=False)
                
                # Procesar y mostrar la imagen
                raw_image = np.frombuffer(image.raw_data, dtype=np.dtype("uint8"))
                raw_image = np.reshape(raw_image, (image.height, image.width, 4))
                bgr_image = raw_image[:, :, :3]
                cv2.imshow("Cámara Síncrona con Tráfico", bgr_image)

                if cv2.waitKey(1) == ord('q'):
                    break
            except queue.Empty:
                continue

    finally:
        print("Limpiando y restaurando la configuración...")
        # Restaurar la configuración original del mundo
        world.apply_settings(original_settings)
        
        # Destruir todos los actores que hemos creado
        client.apply_batch([carla.command.DestroyActor(x) for x in actor_list])
        cv2.destroyAllWindows()
        print("Limpieza completa.")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\nCancelado por el usuario.')