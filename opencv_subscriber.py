# opencv_subscriber.py (MODIFICADO)

import cv2
import numpy as np
import zmq
import torch
import time
from ultralytics import YOLO
from deep_sort_realtime.deepsort_tracker import DeepSort 
# =============================================================================
# INICIO: CÓDIGO DEL MODELO DE VISIÓN (de detección_de_vehículos.py)
# =============================================================================

# Clases de vehículos del dataset COCO que nos interesan
COCO_VEHICLES = {1: "bicycle", 2: "car", 3: "motorcycle", 5: "bus", 7: "truck"}

class YoloDetector:
    def __init__(self, model_name="yolo11n.pt", conf=0.25, imgsz=640):
        self.model = YOLO(model_name)
        self.device = "cuda:0" if torch.cuda.is_available() else "cpu"
        print(f"Usando dispositivo para YOLO: {self.device}")
        self.conf = conf
        self.imgsz = imgsz

    def infer(self, frame):
        """ Ejecuta la inferencia en un frame. """
        results = self.model.predict(
            source=frame,
            imgsz=self.imgsz,
            conf=self.conf,
            device=self.device,
            verbose=False
        )[0]
        
        boxes = results.boxes.xyxy.cpu().numpy()
        confs = results.boxes.conf.cpu().numpy()
        clss = results.boxes.cls.cpu().numpy().astype(int)

        # Filtrar solo las clases de vehículos que nos interesan
        mask = np.array([c in COCO_VEHICLES for c in clss], dtype=bool)
        
        return boxes[mask], confs[mask], [COCO_VEHICLES[c] for c in clss[mask]]




class VehicleTracker:
    def __init__(self):
        self.tracker = DeepSort(max_age=10, n_init=3, nms_max_overlap=0.7)

    # Ahora recibe 'timestamp' en lugar de 'dt'
    def update(self, boxes, scores, frame, timestamp):
        detections = []
        for (x1, y1, x2, y2), score in zip(boxes, scores):
            w, h = x2 - x1, y2 - y1
            detections.append([[float(x1), float(y1), float(w), float(h)], float(score)])

        # Usamos el parámetro 'today' para pasar el timestamp de la simulación
        tracks = self.tracker.update_tracks(detections, frame=frame, today=timestamp)
        
        out_boxes, out_ids = [], []
        for t in tracks:
            if not t.is_confirmed():
                continue
            l, t_, r, b = t.to_ltrb()
            out_boxes.append([l, t_, r, b])
            out_ids.append(int(t.track_id))
            
        return np.array(out_boxes), np.array(out_ids)

class VisionTrackerBlock:
    def __init__(self):
        self.detector = YoloDetector()
        self.tracker = VehicleTracker()
        self.fps = None
        self.alpha = 0.1

    def process(self, frame, timestamp):
        t0 = time.time()
        
        boxes_det, confs_det, _ = self.detector.infer(frame)
        
        # Pasamos el timestamp al tracker
        boxes_trk, ids_trk = self.tracker.update(boxes_det, confs_det, frame, timestamp=timestamp)

        processing_time = time.time() - t0
        current_fps = 1.0 / processing_time if processing_time > 0 else 0
        if self.fps is None:
            self.fps = current_fps
        else:
            self.fps = (1 - self.alpha) * self.fps + self.alpha * current_fps

        return boxes_trk, ids_trk, self.fps

# =============================================================================
# FIN: CÓDIGO DEL MODELO DE VISIÓN
# =============================================================================

def main():
    # --- Configuración de ZeroMQ ---
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.setsockopt(zmq.CONFLATE, 1)
    socket.connect("tcp://localhost:5555")
    socket.setsockopt_string(zmq.SUBSCRIBE, '')
    print("ZMQ Subscriber conectado al puerto 5555 (en modo CONFLATE)")

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
            # Ya no calculamos 'dt', solo extraemos el timestamp
            current_timestamp = metadata['timestamp']

            # --- PROCESAR IMAGEN CON EL MODELO DE VISIÓN ---
            image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
            
            # Pasamos el 'timestamp' directamente al sistema de visión
            boxes, ids, fps_val = vision_system.process(image_rgb, current_timestamp)

            # ... (El resto del código de dibujo y visualización no cambia) ...
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
    # No olvides copiar las clases del modelo de visión aquí arriba
    try:
        main()
    except KeyboardInterrupt:
        print('\nCancelado por el usuario.')