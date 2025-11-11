# opencv_subscriber.py (MODIFICADO)

import cv2
import numpy as np
import zmq
import argparse

from core.inference_class import VisionTrackerBlock

def main():
    argparser = argparse.ArgumentParser(
        description=__doc__)
    argparser.add_argument(
        '-p', '--port',
        metavar='P',
        default=5555,
        type=int,
        help='ZMQ port to listen to (default: 5555)')
    args = argparser.parse_args()

    # --- Configuración de ZeroMQ ---
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.setsockopt(zmq.CONFLATE, 1)
    socket.connect("tcp://localhost:{}".format(args.port))
    socket.setsockopt_string(zmq.SUBSCRIBE, '')
    print("ZMQ Subscriber conectado al puerto {} (en modo CONFLATE)".format(args.port))

    vision_system = VisionTrackerBlock()
    WINDOW_NAME = "Cámara del Semáforo (Visión Artificial)"
    roi_points = np.array([(0, 300), (800, 300), (800, 0), (0, 0)], np.int32)

    try:
        while True:
            # --- Recibir paquete de datos de ZMQ ---
            data_package = socket.recv_pyobj()
            
            metadata = data_package['metadata']
            image_rgba = data_package['image']
            image_bgr = image_rgba[:, :, :3].copy()

            # --- OBTENER TIMESTAMP ---
            current_timestamp = metadata['timestamp']

            # --- PROCESAR IMAGEN CON EL MODELO DE VISIÓN ---
            image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)

            boxes, ids, fps_val = vision_system.process(image_rgb, current_timestamp)
            
            # --- VISUALIZAR RESULTADOS ---
            cv2.polylines(image_bgr, [roi_points], isClosed=True, color=(255, 0, 0), thickness=2)
            inside_roi_ids = set()
            for box, track_id in zip(boxes, ids):
                x1, y1, x2, y2 = map(int, box)
                cv2.rectangle(image_bgr, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(image_bgr, f"ID {track_id}", (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                center_point = (int((x1 + x2) / 2), int((y1 + y2) / 2))
                if cv2.pointPolygonTest(roi_points, center_point, False) >= 0:
                    inside_roi_ids.add(track_id)
            count_roi = len(inside_roi_ids)
            info_text = f"FPS: {fps_val:.1f} | Vehiculos en ROI: {count_roi}"
            cv2.putText(image_bgr, info_text, (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 0), 4, cv2.LINE_AA)
            cv2.putText(image_bgr, info_text, (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2, cv2.LINE_AA)
            cv2.imshow(WINDOW_NAME, image_bgr)

            if cv2.waitKey(1) == ord('q'):
                break
    
    finally:
        print("\nCerrando ventanas...")
        cv2.destroyAllWindows()
        socket.close()
        context.term()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\nCancelado por el usuario.')