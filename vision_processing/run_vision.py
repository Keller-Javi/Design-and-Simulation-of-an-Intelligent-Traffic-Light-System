import cv2
import argparse
from core.inference_class import VisionTrackerBlock
from core.utils import load_camera_config, process_frame
from core.timing_algorithms import TimingAlgorithms
from core.zmq_utils import VisionPublisher, VisionSubscriber

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

    # --- Configuración de ZeroMQ ---
    zmq_vision = VisionSubscriber(port=5555)
    zmq_vision_pub = VisionPublisher(port=5557)
    
    # --- Bucle principal de recepción de imágenes ---
    print("Iniciando recepción de imágenes... Presione 'q' para salir.")
    try:
        while True:
            # --- Cámara 1 ---
            data = zmq_vision.receive_frame()

            if data:
                sem_A, sem_B = process_frame(data["image1"], cam1, vision_cam1)
                sem_C, sem_D = process_frame(data["image2"], cam2, vision_cam2)

                sem_counts = {
                    "A": sem_A,
                    "B": sem_B,
                    "C": sem_C,
                    "D": sem_D
                }

                timing_output = timing_algorithm.update(sem_counts)

                zmq_vision_pub.send_decision(timing_output)
            else:
                continue

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    finally:
        cv2.destroyAllWindows()
        zmq_vision.close()
        zmq_vision_pub.close()
        print("Cerrado correctamente")


if __name__ == "__main__":
    main()