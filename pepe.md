# Proyecto de Detección Semiautomática de Fauna

Este proyecto tiene como objetivo desarrollar una aplicación de escritorio para procesar (preclasificar automáticamente) imágenes provenientes de cámaras trampa, con el fin de identificar imágenes con presencia de fauna, ahorrando tiempo valioso y facilitando el análisis de datos de los especialistas.

## Uso del Proyecto

Para utilizar la aplicación, sigue estos pasos:

1. Se sugiere la utilización de un entorno virtual dedicado (virtualenv, por ejemplo)
2. Clonar el repositorio desde GitHub.
3. Instalar las dependencias necesarias utilizando `pip install -r requirements.txt`.
4. Ejecutar la aplicación ejecutando `python app/main.py`.
5. Seguir las instrucciones en la interfaz para seleccionar la carpeta de imágenes, configurar el modelo, procesar las imágenes y analizar los resultados.

## Estructura del Proyecto

El proyecto estará organizado bajo la siguiente estructura de directorios:

- **app**: Contiene la aplicación Kivy, incluyendo los screens, la lógica de cada screen, los modelos de inteligencia artificial y el procesamiento de imágenes.
  - **screens**: Archivos `.kv` para definir la interfaz de cada screen.
  - **logic**: Archivos `.py` para la lógica de cada screen.
  - **models**: Modelos de inteligencia artificial para el procesamiento de imágenes.
  - **processing**: Módulos para el procesamiento y análisis de las imágenes.
- **config**: Almacena archivos de configuración para los modelos de visión.
- **data**: Directorio para almacenar datos, como las imágenes de entrada y los resultados del análisis.

```
proyecto_fauna_clustering/
│
├── app/
│   ├── screens/                     # Directorio para almacenar los screens de la interfaz
│   │   ├── selection_screen.kv      # Screen de selección de carpeta
│   │   ├── config_screen.kv         # Screen de configuración del modelo
│   │   ├── processing_screen.kv     # Screen de procesamiento de imágenes
│   │   ├── analysis_screen.kv       # Screen de análisis de resultados
│   │   ├── postprocessing_screen.kv # Screen de post-procesamiento
│   │   └── ...
│   ├── logic/                       # Directorio para la lógica de cada screen
│   │   ├── selection_screen.py      # Lógica para el screen de selección de carpeta
│   │   ├── config_screen.py         # Lógica para el screen de configuración del modelo
│   │   ├── processing_screen.py     # Lógica para el screen de procesamiento de imágenes
│   │   ├── analysis_screen.py       # Lógica para el screen de análisis de resultados
│   │   ├── postprocessing_screen.py # Lógica para el screen de post-procesamiento
│   │   └── ...
│   ├── models/                      # Directorio para almacenar los modelos de inteligencia artificial
│   │   ├── embedding_model.h5       # Modelo de embedding pre-entrenado
│   │   └── ...
│   ├── processing/                  # Directorio para el procesamiento de imágenes
│   │   ├── image_processing.py      # Módulo para procesamiento de imágenes
│   │   ├── analysis.py              # Módulo para análisis de resultados
│   │   └── ...
│   ├── main.py                      # Archivo principal de la aplicación
│   └── ...
│
├── config/                          # Directorio para archivos de configuración
│   ├── model_config.yaml            # Configuración de los modelos de visión
│   └── ...
│
├── data/                            # Directorio para almacenar datos (imágenes, resultados)
│   ├── input_images/                # Directorio para las imágenes de entrada
│   ├── processed_images/            # Directorio para las imágenes procesadas
│   ├── results/                     # Directorio para los resultados del análisis
│   └── ...
│
├── docs/                            # Directorio para la documentación
│   ├── app_features.md              # Documentación de las características de la aplicación
│   ├── development.md               # Documentación sobre el desarrollo
│   └── ...
│
├── tests/                           # Directorio para pruebas
│   ├── test_image_processing.py     # Pruebas para el módulo de procesamiento de imágenes
│   ├── test_analysis.py             # Pruebas para el módulo de análisis de resultados
│   └── ...
│
├── .gitignore                       # Archivo de configuración para Git
├── requirements.txt                 # Archivo de dependencias del proyecto
└── README.md                        # Archivo README con instrucciones y detalles del proyecto
```

## Contribución

Este proyecto sigue el flujo de trabajo estándar de Git:

1. Crea una nueva rama para trabajar en una nueva función o solución.
2. Realiza los cambios y asegura el cumplimiento de los tests.
3. Realiza un push de los cambios a tu rama.
4. Abre un pull request para revisión.

### Solicitar Nuevas Características

Si tienes una idea para una nueva característica, sigue estos pasos:

1. Abre un "Issue" en el repositorio.
2. Describe la característica que te gustaría ver implementada.
3. Explica por qué esta característica sería útil y cómo debería funcionar.

### Reportar Problemas

Si encuentras un problema o bug, sigue estos pasos:

1. Abre un "Issue" en el repositorio de GitHub.
2. Proporciona un título claro y una descripción detallada del problema.
3. Incluye cualquier mensaje de error relevante y pasos para reproducir el problema.
