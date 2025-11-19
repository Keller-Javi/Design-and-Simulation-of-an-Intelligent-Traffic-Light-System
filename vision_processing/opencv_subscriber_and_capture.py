# opencv_detector_and_recorder.py

import cv2
import numpy as np
import zmq
from datetime import datetime

from core.inference_class import VisionTrackerBlock

def main():
    # --- CONFIGURACIÓN ---
    FRAMES_TO_RECORD = 5000
    RECORD_KEY = ord('r')
    QUIT_KEY = ord('q')

    # --- Configuración de ZeroMQ ---
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.setsockopt(zmq.CONFLATE, 1)
    socket.connect("tcp://localhost:5555")
    socket.setsockopt_string(zmq.SUBSCRIBE, '')
    print("ZMQ Subscriber conectado al puerto 5555 (en modo CONFLATE)")
    print(f"Presiona '{chr(RECORD_KEY).upper()}' para grabar un clip de {FRAMES_TO_RECORD} frames.")
    print(f"Presiona '{chr(QUIT_KEY).upper()}' para salir.")

    vision_system = VisionTrackerBlock()
    WINDOW_NAME = "Cámara del Semáforo (Visión Artificial)"
    roi_points = np.array([(0, 300), (800, 300), (800, 0), (0, 0)], np.int32)

    # --- Variables de estado para la grabación ---
    is_recording = False
    recording_frame_count = 0
    video_writer = None

    try:
        while True:
            # --- Recibir paquete de datos de ZMQ ---
            data_package = socket.recv_pyobj()
            metadata = data_package['metadata']
            image_rgba = data_package['image']
            image_bgr = image_rgba[:, :, :3].copy()

            # --- PROCESAR IMAGEN CON EL MODELO DE VISIÓN ---
            current_timestamp = metadata['timestamp']
            image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
            boxes, ids, fps_val = vision_system.process(image_rgb, current_timestamp)

            # --- DIBUJAR RESULTADOS ---
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

            # --- Lógica de Grabación ---
            key = cv2.waitKey(1) & 0xFF

            if key == QUIT_KEY:
                break

            if key == RECORD_KEY and not is_recording:
                is_recording = True
                recording_frame_count = 0
                timestamp_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                filename = f"detection_recording_{timestamp_str}.mp4"
                height, width, _ = image_bgr.shape
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                record_fps = max(fps_val, 10.0) if fps_val is not None else 20.0
                video_writer = cv2.VideoWriter(filename, fourcc, record_fps, (width, height))
                print(f"\n¡Iniciando grabación! -> Guardando en '{filename}' a ~{record_fps:.1f} FPS")

            if is_recording:
                # El frame que se guarda es el que ya tiene todos los dibujos
                video_writer.write(image_bgr)
                recording_frame_count += 1
                
                cv2.circle(image_bgr, (width - 30, 30), 10, (0, 0, 255), -1)
                cv2.putText(image_bgr, "REC", (width - 70, 37), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                
                if recording_frame_count >= FRAMES_TO_RECORD:
                    is_recording = False
                    video_writer.release()
                    video_writer = None
                    print(f"Grabación finalizada. Video guardado.")

            # Mostrar la imagen final (con el indicador REC si está grabando)
            cv2.imshow(WINDOW_NAME, image_bgr)

    finally:
        print("\nLimpiando y cerrando...")
        if video_writer is not None:
            video_writer.release()
            print("Grabación en curso guardada forzosamente.")
        cv2.destroyAllWindows()
        socket.close()
        context.term()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\nCancelado por el usuario.')