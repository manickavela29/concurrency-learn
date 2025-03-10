'''
# Python program to demonstrate use of a queue to communicate between processes.

# p1 and p2 have a shared queue between them and 
# once they are started they will act based on the data from the queueu

'''
import multiprocessing

def square_list(mylist, q):
    # function to square list of values
    # square the list values and append it to q
    
    for num in mylist:
        q.put(num * num)

def print_queue(q):
    # function to print queue elements
    print("Queue elements:")
    while not q.empty():
        print(q.get())
    print("Queue is now empty!")     

if __name__ == "__main__":
    mylist = [1,2,3,4]
    
    # creating multiprocessing Queue
    q = multiprocessing.Queue()
    
    # creating new processes
    p1 = multiprocessing.Process(target=square_list, args=(mylist, q))
    p2 = multiprocessing.Process(target=print_queue, args=(q,)) # note the comma after q
    
    # starting processes
    p1.start()
    p2.start()
    p1.join()
    
    # p2.start()
    p2.join()