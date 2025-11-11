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