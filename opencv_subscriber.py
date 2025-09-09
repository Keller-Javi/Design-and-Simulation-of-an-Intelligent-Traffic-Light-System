import cv2
import numpy as np
import zmq

def main():
    # --- Configuración de ZeroMQ ---
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.connect("tcp://localhost:5555")
    socket.setsockopt_string(zmq.SUBSCRIBE, '')
    print("ZMQ Subscriber conectado al puerto 5555")

    # Definir un nombre de ventana constante
    WINDOW_NAME = "Cámara del Semáforo (Visión Artificial)"

    try:
        while True:
            # --- Recibir imagen de ZMQ ---
            metadata = socket.recv_pyobj()
            image_data = socket.recv(copy=False)
            
            # Crear el array de numpy a partir de los datos recibidos
            image_array = np.frombuffer(image_data, dtype=np.uint8)
            image_bgr = image_array.reshape(metadata['height'], metadata['width'], 4)[:, :, :3]

            # Creamos una copia explícita para que el array sea escribible
            image_bgr = image_array.reshape(metadata['height'], metadata['width'], 4)[:, :, :3].copy()

            # --- Procesar y mostrar la imagen ---
            
            # Añadir el número de frame sobre la imagen
            frame_text = f"Frame: {metadata['frame']}"
            font = cv2.FONT_HERSHEY_SIMPLEX
            cv2.putText(
                img=image_bgr, 
                text=frame_text, 
                org=(10, 30), # Posición (esquina inferior izquierda del texto)
                fontFace=font, 
                fontScale=1, 
                color=(255, 255, 255), # Color blanco
                thickness=2
            )
            
            # Mostrar la imagen en una ventana
            cv2.imshow(WINDOW_NAME, image_bgr)

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