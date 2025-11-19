import os
import json
import numpy as np
import cv2

def load_camera_config(config_path):
    """Carga un archivo JSON y arma la estructura de ROIs."""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"No existe el archivo: {config_path}")

    with open(config_path, "r") as f:
        cfg = json.load(f)

    rois_cfg = cfg.get("rois", [])
    if not rois_cfg:
        raise ValueError(f"El archivo {config_path} no contiene ROIs.")

    roi_structs = []
    for roi in rois_cfg:
        roi_structs.append({
            "name": roi.get("name", "ROI"),
            "points": np.array(roi.get("points", []), np.int32),
            "color": tuple(roi.get("color", [255, 0, 0]))
        })

    return {
        "port": cfg.get("port"),
        "window_name": cfg.get("window_name", f"Cam {cfg.get('port')}"),
        "rois": roi_structs
    }


def process_frame(data_package, cam_cfg, vision_system):
    metadata = data_package["metadata"]
    image_rgba = data_package["image"]
    image_bgr = image_rgba[:, :, :3].copy()

    timestamp = metadata["timestamp"]

    # Procesamiento del modelo
    image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
    boxes, ids, fps_val = vision_system.process(image_rgb, timestamp)

    # Dibujar ROIs + conteo
    total_counts = {}
    for roi in cam_cfg["rois"]:
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

    cv2.imshow(cam_cfg["window_name"], image_bgr)

    return total_counts.values() 
