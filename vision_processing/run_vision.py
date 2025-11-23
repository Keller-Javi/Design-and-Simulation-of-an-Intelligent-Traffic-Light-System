import cv2
import zmq
import argparse
from core.inference_class import VisionTrackerBlock
from core.utils import load_camera_config, process_frame
from core.timing_algorithms import TimingAlgorithms
from core.zmq_utils import VisionSubscriber, DataPublisher

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--cam1", required=True, help="Config JSON de la cámara 1"
    )
    parser.add_argument(
        "--cam2", required=True, help="Config JSON de la cámara 2"
    )
    args = parser.parse_args()

    # --- Cargar configuración de ambas cámaras ---
    cam1 = load_camera_config(args.cam1)
    cam2 = load_camera_config(args.cam2)

    # --- ZeroMQ ---
    subscriber = VisionSubscriber()

    socket1 = subscriber.add_subscription(cam1["port"])
    socket2 = subscriber.add_subscription(cam2["port"])

    poller = zmq.Poller()
    poller.register(socket1, zmq.POLLIN)
    poller.register(socket2, zmq.POLLIN)
    
    # --- Publicador para enviar datos procesados ---
    publisher = DataPublisher(port=5557)

    # Un solo modelo de visión para ambas cámaras
    vision_cam1 = VisionTrackerBlock(
        confidence_threshold=0.25,
        max_age=1,
        n_init=5,
        nms_max_overlap=0.9
    )

    vision_cam2 = VisionTrackerBlock(
        confidence_threshold=0.25,
        max_age=1,
        n_init=5,
        nms_max_overlap=0.9
    )

    sem_A, sem_B, sem_C, sem_D = 0, 0, 0, 0
    timing_algorithm = TimingAlgorithms(algorithm_type="method1")

    print("Iniciando recepción de imágenes... Presione 'q' para salir.")
    try:
        while True:

            events = dict(poller.poll(timeout=10))  # no bloquea infinitamente

            # --- Cámara 1 ---
            if socket1 in events:
                data = socket1.recv_pyobj()
                sem_A, sem_B = process_frame(data, cam1, vision_cam1)

            # --- Cámara 2 ---
            if socket2 in events:
                data = socket2.recv_pyobj()
                sem_C, sem_D = process_frame(data, cam2, vision_cam2)
            
            sem_counts = {
                "A": sem_A,
                "B": sem_B,
                "C": sem_C,
                "D": sem_D
            }

            #print(f"Conteos de semáforos: {sem_counts}")

            timing_output = timing_algorithm.update(sem_counts)

            publisher.send_data(timing_output)
            #publisher.send_data(sem_counts)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    finally:
        cv2.destroyAllWindows()
        subscriber.close()
        publisher.close()
        print("Cerrado correctamente")


if __name__ == "__main__":
    main()