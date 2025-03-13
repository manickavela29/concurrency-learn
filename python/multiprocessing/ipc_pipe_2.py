from multiprocessing import Process, Pipe

class MyProcess(Process):
    def __init__(self):
        super().__init__()
        self.front_pipe, self.back_pipe = Pipe()

    #Backend
    def run(self):
        self.active = True
        while self.active:
            self.active = self.listenFront_()
        print("Backend: Exiting...")

    def listenFront_(self):
        message = self.back_pipe.recv()
        print(f"Backend: Received message: {message}")
        if message == "stop":
            return False
        elif message == "ping":
            self.ping_()
            return True
        else:
            print(f"Backend: Unknown message {message}")
            return True

    def ping_(self):
        print(f"Backend : got ping from frontend")
        self.front_pipe.send("pong")

    # Frontend
    def ping(self):
        self.front_pipe.send("ping")
        response = self.back_pipe.recv()
        print(f"Frontend: Received response: {response}")

    def stop(self):
        self.front_pipe.send("stop")
        self.join

if __name__ == "__main__":
    p = MyProcess()
    print("Starting process")
    p.start()
    print(f"Process started, started pinging")
    p.ping()
    print(f"Ping sent, waiting for response and stopping")
    p.stop()
    print("Stopping process")