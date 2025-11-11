from ultralytics import YOLO

# Carga tu modelo YOLOv8
model = YOLO('yolo11n.pt') # Usamos el mismo modelo 'nano'

# Exporta a formato ONNX
model.export(format='onnx')

print("✅ Modelo exportado a 'yolov8n.onnx'")