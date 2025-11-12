import cv2
import numpy as np
import zmq
import argparse
import os
import json

from core.inference_class import VisionTrackerBlock

def main():
    argparser = argparse.ArgumentParser(
        description=__doc__)
    argparser.add_argument(
        '-c', '--config',
        type=str,
        required=True,
        help='Ruta al archivo JSON de configuración de la cámara (ej: config_cam1.json)'
    )
    args = argparser.parse_args()

    # --- Cargar configuración desde JSON ---
    if not os.path.exists(args.config):
        raise FileNotFoundError(f"No se encontró el archivo de configuración: {args.config}")

    with open(args.config, 'r') as f:
        config = json.load(f)

    port = config.get("port", 5555)
    window_name = config.get("window_name", f"Cámara {port}")
    rois = config.get("rois", [])

    if not rois:
        raise ValueError("El archivo de configuración no contiene ninguna ROI definida.")

    roi_structs = []
    for roi in rois:
        roi_points = np.array(roi.get("points", []), np.int32)
        roi_color = tuple(roi.get("color", [255, 0, 0]))
        roi_name = roi.get("name", "ROI")
        roi_structs.append({
            "name": roi_name,
            "points": roi_points,
            "color": roi_color
        })

    # --- Configuración de ZeroMQ ---
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.setsockopt(zmq.CONFLATE, 1)
    socket.connect("tcp://localhost:{}".format(port))
    socket.setsockopt_string(zmq.SUBSCRIBE, '')
    print("ZMQ Subscriber conectado al puerto {} (en modo CONFLATE)".format(port))

    vision_system = VisionTrackerBlock(confidence_threshold=0.25, max_age=2, n_init=5, nms_max_overlap=0.8)

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
            # --- Dibujar todas las ROIs ---
            total_counts = {}
            for roi in roi_structs:
                cv2.polylines(image_bgr, [roi["points"]], isClosed=True, color=roi["color"], thickness=2)
                cv2.putText(image_bgr, roi["name"],
                            tuple(roi["points"][0]), cv2.FONT_HERSHEY_SIMPLEX,
                            0.8, roi["color"], 2, cv2.LINE_AA)

                inside_ids = set()
                for box, track_id in zip(boxes, ids):
                    x1, y1, x2, y2 = map(int, box)
                    center_point = (int((x1 + x2) / 2), int((y1 + y2) / 2))
                    if cv2.pointPolygonTest(roi["points"], center_point, False) >= 0:
                        inside_ids.add(track_id)

                total_counts[roi["name"]] = len(inside_ids)

            # --- Dibujar detecciones ---
            for box, track_id in zip(boxes, ids):
                x1, y1, x2, y2 = map(int, box)
                cv2.rectangle(image_bgr, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(image_bgr, f"ID {track_id}", (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

            # --- Información en pantalla ---
            info_lines = [f"FPS: {fps_val:.1f}"]
            for name, count in total_counts.items():
                info_lines.append(f"{name}: {count}")

            y_offset = 30
            for line in info_lines:
                cv2.putText(image_bgr, line, (10, y_offset),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 4, cv2.LINE_AA)
                cv2.putText(image_bgr, line, (10, y_offset),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2, cv2.LINE_AA)
                y_offset += 30

            cv2.imshow(window_name, image_bgr)

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