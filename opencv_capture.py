# opencv_recorder.py

import cv2
import numpy as np
import zmq
import time
from datetime import datetime

def main():
    # --- CONFIGURACIÓN ---
    # Puedes cambiar estos valores según tus necesidades
    WINDOW_NAME = "Visor y Grabador de CARLA"
    FRAMES_TO_RECORD = 10000 # Número de frames a grabar por video (ej. 300 frames a 20 FPS = 15 segundos)
    RECORD_KEY = ord('r')   # Tecla para iniciar la grabación
    QUIT_KEY = ord('q')     # Tecla para salir

    # --- Configuración de ZeroMQ ---
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    # La opción CONFLATE sigue siendo útil para asegurar que siempre vemos el frame más reciente
    socket.setsockopt(zmq.CONFLATE, 1)
    socket.connect("tcp://localhost:5555")
    socket.setsockopt_string(zmq.SUBSCRIBE, '')
    print("ZMQ Subscriber conectado al puerto 5555.")
    print(f"Presiona '{chr(RECORD_KEY).upper()}' para grabar un clip de {FRAMES_TO_RECORD} frames.")
    print(f"Presiona '{chr(QUIT_KEY).upper()}' para salir.")

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

            # --- Lógica de Grabación ---
            key = cv2.waitKey(1) & 0xFF

            # Salir del programa
            if key == QUIT_KEY:
                print("Saliendo...")
                break

            # Iniciar una nueva grabación
            if key == RECORD_KEY and not is_recording:
                is_recording = True
                recording_frame_count = 0
                
                # Generar un nombre de archivo único con fecha y hora
                timestamp_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                filename = f"recording_{timestamp_str}.mp4"
                
                # Configurar el VideoWriter de OpenCV
                height, width, _ = image_bgr.shape
                fourcc = cv2.VideoWriter_fourcc(*'mp4v') # Codec para .mp4
                # Usamos 20.0 FPS como un valor razonable, ya que la simulación está a 20 FPS
                video_writer = cv2.VideoWriter(filename, fourcc, 20.0, (width, height))
                
                print(f"\n¡Iniciando grabación! -> Guardando en '{filename}'")

            # Si estamos en modo grabación
            if is_recording:
                # Escribir el frame actual en el archivo de video
                video_writer.write(image_bgr)
                recording_frame_count += 1
                
                # Dibujar un indicador visual en la pantalla
                cv2.circle(image_bgr, (30, 30), 10, (0, 0, 255), -1) # Círculo rojo
                cv2.putText(image_bgr, "REC", (50, 37), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                
                # Comprobar si hemos alcanzado el número de frames deseado
                if recording_frame_count >= FRAMES_TO_RECORD:
                    is_recording = False
                    video_writer.release() # Finalizar y guardar el video
                    video_writer = None
                    print(f"Grabación finalizada. Video guardado.")

            # Mostrar siempre la imagen en la ventana
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