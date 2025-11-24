# 🚦Proyecto GreenLight

**Descripción breve:**  
Este proyecto corresponde al trabajo final de la **Carrera de Ingeniería en Computación** de la **Facultad de Ingeniería de la UNaM**.  
Consiste en una **simulación de semáforos inteligentes** utilizando **CARLA Simulator** y su **API en Python**.

---
## Estructura del proyecto
```
.
├── carla_sim
│   ├── core
│   │   ├── dynamic_weather.py
│   │   ├── setup_camera.py
│   │   ├── setup_world.py
│   │   ├── spawn_utils.py
│   │   ├── traffic_metrics.py
│   │   └── zqm_publisher.py
│   ├── run_simulator.py
│   └── spectator.py
├── vision_processing
│   ├── core
│   │   ├── inference_class.py
│   │   ├── timing_algorithms.py
│   │   ├── utils.py
│   │   └── zmq_utils.py
│   ├── model.py
│   ├── opencv_capture.py
│   └── run_vision.py
├── .gitignore
└── requierements.txt
```

Descripción general de los distintos modulos:

### `run_simulator.py`
Encargado de:
- Cargar y configurar el mundo de la simulación (mapa, clima, tráfico, etc.).
- Administrar parámetros dinámicos como el **clima** y el **tránsito vehicular**.
- Transmitir los **frames capturados por las cámaras** a través de **puertos ZMQ**.
- Guardar métricas del tráfico en un archivo csv.

> Estos frames se transfieren por defecto mediante los puertos 5555 (cámara 1) y 5556 (cámara 2).
### `run_vision.py`
Encargado de:
- **Leer un puerto específico** para recibir los frames transmitidos.
- **Configurar los parametros** de YOLO y DeepSort, como confianza, edad y superposición de objetos. 
- **Realizar inferencias** sobre los frames mediante un modelo de detección (por ejemplo, YOLO).
- **Visualizar** los resultados de la inferencia en tiempo real.
- **Tomar desiciones** en base a los conteos de los vehículos de cada semáforo.
- **Actualizar la temporización** en base al algoritmo seleccionado.  

Este necesita dos archivos de configuración para funcionar, es uno para cada cámara y es un archivo formato json que contiene lo siguiente:
```yaml
{
  "receive_port": 5555,
  "send_port": 5557,
  "rois_A": [
    {
      "name": "Semaforo A",
      "points": [[25, 285], [65, 285], [262, 387], [169, 413]],
      "color": [255, 0, 0]
    },
    {
      "name": "Semaforo B",
      "points": [[451, 367], [528, 389], [596, 307], [546, 285]],
      "color": [0, 255, 255]
    }
  ],
  "rois_B": [
    {
      "name": "Semaforo C",
      "points": [[265, 334], [130, 252], [97, 255], [184, 352]],
      "color": [255, 255, 0]
    },
    {
      "name": "Semaforo D",
      "points": [[463, 320], [529, 338], [699, 259], [668, 256]],
      "color": [0, 0, 255]
    }
  ]
}
```
> Ejemplo de como ejecutar:  
> `python .\vision_processing\run_vision.py --config vision_processing/config/config_cam.json`

### `Modularizaciones`
- Tanto `run_simulator` como `run_vision` cuentan con submódulos dentro de la carpeta **core**, los cuales encapsulan funcionalidades específicas. Los nombres de los módulos describen claramente su propósito.

### `Scripts auxiliares`

Estos scripts no se utilizan actualmente, pero pueden ser útiles para desarrollo o depuración:

- **`spectator.py`**: Muestra la ubicación en tiempo real de la cámara libre de la simulación.  
- **`model.py`**: Permite exportar el modelo YOLO a otros formatos.  
- **`opencv_capture.py`**: Captura los frames recibidos por el puerto y los guarda en formato `.mp4`.

---

## Dependencias

Instalar las dependencias necesarias con:

```bash
pip install -r requirements.txt
