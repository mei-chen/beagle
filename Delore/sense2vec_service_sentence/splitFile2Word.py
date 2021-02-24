from threading import Thread
from Queue import Queue

def process_file(f, source_filename):
    """
    Apply the function `f` to each line of `source_filename` and write
    the results to `target_filename`. Each call to `f` is evaluated in
    a separate thread.
    """
    worker_queue = Queue()
    finished = object()

    def process(queue, line):
        "Process `line` and put the result on `queue`."
        #print f(line)
        queue.put(f(line))

    def read():
        """
        Read `source_filename`, create an output queue and a worker
        thread for every line, and put that worker's output queue onto
        `worker_queue`.
        """
        with open(source_filename, 'r') as source:
            for line in source:
                queue = Queue()
                Thread(target = process, args=(queue, line)).start()
                worker_queue.put(queue)
        worker_queue.put(finished)

    Thread(target = read).start()
    outputList=[]
    for output in iter(worker_queue.get, finished):
        outputList=outputList+output.get()
    return outputList

def splitRemoveNewLine(line):
    return line.replace('\n','').split(' ')

# if __name__ == "__main__":
#
#     print process_file(split, '/mnt/corpus/EUlaw_no_tagger/corpus_EUlaw.txt')