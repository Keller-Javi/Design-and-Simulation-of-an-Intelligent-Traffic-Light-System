import zmq

class ZMQPublisher:
    def __init__(self, port=5555):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PUB)
        self.socket.bind(f"tcp://*:{port}")
        print(f"ZMQ Publisher listo en el puerto {port}")

    def send_image(self, image, array):
        data_package = {
            'metadata': {
                'width': image.width,
                'height': image.height,
                'frame': image.frame,
                'timestamp': image.timestamp
            },
            'image': array
        }
        self.socket.send_pyobj(data_package)
    
    def close(self):
        self.socket.close()
        self.context.term()
        print("ZMQ Publisher cerrado.")

class ZMQSubscriber:
    def __init__(self, port):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.SUB)
        self.socket.setsockopt(zmq.CONFLATE, 1)
        self.socket.connect(f"tcp://localhost:{port}")
        self.socket.setsockopt_string(zmq.SUBSCRIBE, "")
        self.subscriber_sockets = []

    def reseive(self):
        try:
            return self.socket.recv_pyobj(flags=zmq.NOBLOCK)
        except zmq.Again:
            return None
    
    def close(self):
        self.socket.close()
        self.context.term()
        print("[SUB] Cerrado correctamente")