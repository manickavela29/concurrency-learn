import zmq

HOST = "127.0.0.1"
PORT = 5001

# Create a socket instance
context = zmq.Context()
socket = context.socket(zmq.SUB)

# Connect to bound socket
socket.connect(f"tcp://{HOST}:{PORT}")

# Subscribe to all topics
socket.subscribe(b"")
message = socket.recv_string()
print(f"Received message: {message}")