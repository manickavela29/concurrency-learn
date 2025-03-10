import multiprocessing

def sender(conn, msgs):
    """
    function to send messages to other end of pipe
    """
    for msg in msgs:
        conn.send(msg)
        print(f"Sent the message: {msg}")
    conn.close()
    
def receiver(conn):
    """
    function to receive messages from other
    end of pipe
    """
    while 1:
        try:
            msg = conn.recv()
            print(f"Received the message: {msg}")
        except EOFError:
            break
        except KeyboardInterrupt:
            break
    conn.close()

if __name__ == "__main__":
    # messages to be sent
    msgs = ["hello", "hey", "hru?"]
    
    # creating a pipe
    parent_conn, child_conn = multiprocessing.Pipe()
    
    # creating new processes
    p1 = multiprocessing.Process(target=sender, args=(parent_conn, msgs))
    p2 = multiprocessing.Process(target=receiver, args=(child_conn,))
    
    # starting processes
    p1.start()
    p2.start()
    
    # wait until processes finish
    p1.join()
    p2.join()
    print("Finished")

# Output:
# Sent the message: hello
# Received the message: hello
# Sent the message: hey
# Received the message: hey
# Sent the message: hru?
# Received the message: hru?
# Finished