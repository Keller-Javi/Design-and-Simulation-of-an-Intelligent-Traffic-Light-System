# opencv_detector_and_recorder.py

import cv2
import numpy as np
import zmq
import torch
import time
from ultralytics import YOLO
from deep_sort_realtime.deepsort_tracker import DeepSort
from datetime import datetime

# =============================================================================
# INICIO: CÓDIGO DEL MODELO DE VISIÓN
# =============================================================================

#COCO_VEHICLES = {1: "bicycle", 2: "car", 3: "motorcycle", 5: "bus", 7: "truck"}
COCO_VEHICLES = {0: "vehicle"}

class YoloDetector:
    def __init__(self, model_name="best.pt", conf=0.2, imgsz=640):
        self.model = YOLO(model_name)
        self.device = "cuda:0" if torch.cuda.is_available() else "cpu"
        print(f"Usando dispositivo para YOLO: {self.device}")
        self.conf = conf
        self.imgsz = imgsz

    def infer(self, frame):
        results = self.model.predict(
            source=frame, imgsz=self.imgsz, conf=self.conf,
            device=self.device, verbose=False
        )[0]
        boxes = results.boxes.xyxy.cpu().numpy()
        confs = results.boxes.conf.cpu().numpy()
        clss = results.boxes.cls.cpu().numpy().astype(int)
        mask = np.array([c in COCO_VEHICLES for c in clss], dtype=bool)
        return boxes[mask], confs[mask], [COCO_VEHICLES[c] for c in clss[mask]]

class VehicleTracker:
    def __init__(self):
        self.tracker = DeepSort(max_age=3, n_init=3, nms_max_overlap=0.7)

    def update(self, boxes, scores, frame, timestamp):
        detections = []
        for (x1, y1, x2, y2), score in zip(boxes, scores):
            w, h = x2 - x1, y2 - y1
            detections.append([[float(x1), float(y1), float(w), float(h)], float(score)])
        tracks = self.tracker.update_tracks(detections, frame=frame, today=timestamp)
        out_boxes, out_ids = [], []
        for t in tracks:
            if not t.is_confirmed(): continue
            l, t_, r, b = t.to_ltrb()
            out_boxes.append([l, t_, r, b]); out_ids.append(int(t.track_id))
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
        boxes_trk, ids_trk = self.tracker.update(boxes_det, confs_det, frame, timestamp=timestamp)
        processing_time = time.time() - t0
        current_fps = 1.0 / processing_time if processing_time > 0 else 0
        if self.fps is None: self.fps = current_fps
        else: self.fps = (1 - self.alpha) * self.fps + self.alpha * current_fps
        return boxes_trk, ids_trk, self.fps

# =============================================================================
# FIN: CÓDIGO DEL MODELO DE VISIÓN
# =============================================================================

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