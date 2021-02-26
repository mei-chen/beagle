import time

LEVEL = 1

def timeit(func):
    def wrapper(*arg, **kw):
        t1 = time.time()
        global LEVEL
        print ('----' * LEVEL) + '> Started %s' % func.__name__
        LEVEL += 1
        result = func(*arg, **kw)
        LEVEL -= 1
        t2 = time.time()
        print ('----' * LEVEL) + '> Finished %s - %0.3fms.' % (func.__name__, (t2 - t1) * 1000.)
        return result
    return wrapper