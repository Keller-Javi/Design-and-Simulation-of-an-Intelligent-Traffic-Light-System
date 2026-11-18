from ultralytics import YOLO

model = YOLO('yolo26s.pt')

# Exporta a formato ONNX
model.export(format='onnx')

print("✅ Modelo exportado a 'yolo11n.onnx'")