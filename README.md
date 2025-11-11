# 🚦Proyecto GreenLight

**Descripción breve:**  
Este proyecto corresponde al trabajo final de la **Carrera de Ingeniería en Computación** de la **Facultad de Ingeniería de la UNaM**.  
Consiste en una **simulación de semáforos inteligentes** utilizando **CARLA Simulator** y su **API en Python**.

---
## Estructura del proyecto
```
.
├── carla_publisher
│   ├── core
│   │   ├── dynamic_weather.py
│   │   ├── setup_camera.py
│   │   ├── setup_world.py
│   │   ├── spawn_utils.py
│   │   └── zqm_publisher.py
│   ├── carla_publisher.py
│   └── spectator.py
├── opencv_subscriber
│   ├── core
│   │   └── inference_class.py
│   ├── model.py
│   ├── opencv_capture.py
│   └── opencv_subscriber.py
├── .gitignore
└── requierements.txt
```

---
## Descripción de los módulos principales

### `carla_publisher.py`
Encargado de:
- Cargar y configurar el mundo de la simulación (mapa, clima, tráfico, etc.).
- Administrar parámetros dinámicos como el **clima** y el **tránsito vehicular**.
- Transmitir los **frames capturados por las cámaras** a través de **puertos ZMQ**.

### `opencv_subscriber.py`
Encargado de:
- **Leer un puerto específico** para recibir los frames transmitidos.
- **Realizar inferencias** sobre los frames mediante un modelo de detección (por ejemplo, YOLO).
- **Visualizar** los resultados de la inferencia en tiempo real.  
> Se puede especificar el puerto a utilizar con el parámetro:  
> `-p=[puerto]`

---

## Scripts auxiliares

Estos scripts no se utilizan actualmente, pero pueden ser útiles para desarrollo o depuración:

- **`spectator.py`**: Muestra la ubicación en tiempo real de la cámara libre de la simulación.  
- **`model.py`**: Permite exportar el modelo YOLO a otros formatos.  
- **`opencv_capture.py`**: Captura los frames recibidos por el puerto y los guarda en formato `.mp4`.

---

## Dependencias

Instalar las dependencias necesarias con:

```bash
pip install -r requirements.txt
