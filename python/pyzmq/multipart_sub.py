# multipart_sub.py
import zmq

host = "127.0.0.1"
port = "5001"

# Creates a socket instance
context = zmq.Context()
socket = context.socket(zmq.SUB)

# Connects to a bound socket
socket.connect("tcp://{}:{}".format(host, port))

# Subscribes to ML topics
socket.subscribe("ML")

# Receives a multipart message
print(socket.recv_multipart())