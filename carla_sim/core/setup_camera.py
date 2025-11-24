import queue
import carla
import numpy as np

def add_camera(world, blueprint_library, target_location, target_rotation):
    camera_bp = blueprint_library.find('sensor.camera.rgb')
    camera_bp.set_attribute('image_size_x', '800')
    camera_bp.set_attribute('image_size_y', '600')
        
    #camera_transform = carla.Transform(carla.Location(x=-4,z=4.5), carla.Rotation(pitch=-18.22, yaw=90.85, roll=0.00))
    camera_transform = carla.Transform(target_location, target_rotation)
    camera = world.spawn_actor(camera_bp, camera_transform)

    image_queue = queue.Queue()
    camera.listen(image_queue.put)

    return camera, image_queue

def prepare_camera_data(image_queue_1, image_queue_2):
    data = {
        "image1": None,
        "image2": None
    }

    for idx, image_queue in enumerate([image_queue_1, image_queue_2], start=1):
        key = f"image{idx}"
        try:
            image = image_queue.get(block=False)

            array = np.frombuffer(image.raw_data, dtype=np.uint8)
            array = np.reshape(array, (image.height, image.width, 4))

            data[key] = {
                'metadata': {
                    'width': image.width,
                    'height': image.height,
                    'frame': image.frame,
                    'timestamp': image.timestamp,
                },
                'image': array
            }

        except queue.Empty:
            print(f"No se recibió imagen de la cámara {key}.")

    return data