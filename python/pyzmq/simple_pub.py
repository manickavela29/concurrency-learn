import zmq
import time

HOST = "127.0.0.1"
PORT = 5001

#creates a context center
context = zmq.Context()
socket = context.socket(zmq.PUB)

socket.bind(f"tcp://{HOST}:{PORT}")

# bind is asyncronous, so we need to wait for the connection to be established
# time.sleep(1) # new sleep statement

socket.send_string("Hello World")
