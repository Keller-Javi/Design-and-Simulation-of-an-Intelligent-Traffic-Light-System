import zmq

class DataPublisher:
    def __init__(self, port=5557):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PUB)
        self.socket.bind(f"tcp://*:{port}")
        print(f"[PUB] Publisher listo en el puerto {port}")

    def send_data(self, data_package):
        self.socket.send_pyobj(data_package)

    def close(self):
        self.socket.close()
        self.context.term()
        print("[PUB] Cerrado correctamente")


class VisionSubscriber:
    def __init__(self):
        self.context = zmq.Context()
        self.subscriber_sockets = []

    def add_subscription(self, port):
        socket = self.context.socket(zmq.SUB)
        socket.setsockopt(zmq.CONFLATE, 1)
        socket.connect(f"tcp://localhost:{port}")
        socket.setsockopt_string(zmq.SUBSCRIBE, "")
        print(f"[SUB] Suscrito al puerto {port}")

        self.subscriber_sockets.append(socket)
        return socket

    def close(self):
        for sock in self.subscriber_sockets:
            sock.close()
        self.context.term()
        print("[SUB] Cerrado correctamente")
