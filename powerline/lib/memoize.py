import cPickle as pickle
import time


class memoize(object):
    '''Memoization decorator with timout.

    http://code.activestate.com/recipes/325905-memoize-decorator-with-timeout/
    '''

    def __init__(self, timeout, additional_key=None, filename=None):
        self.timeout = timeout
        self.additional_key = additional_key
        self.filename = filename
        self.caches = {}

    def __call__(self, f):

        def func(*args, **kwargs):

            if self.filename:
                with open(self.filename, 'rb') as fileobj:
                    try:
                        self.caches = pickle.load(fileobj)
                    except EOFError:
                        pass

            key = (args, tuple(kwargs.items()))

            if self.additional_key:
                key += (self.additional_key(), )

            key = str(key)
            result = self.caches.get(key, None)

            if result is None or time.time() - result[1] > self.timeout:
                result = self.caches[key] = f(*args, **kwargs), time.time()

            if self.filename:
                with open(self.filename, 'wb') as fileobj:
                    pickle.dump(self.caches, fileobj)
                    fileobj.close()

            return result[0]

        func.func_name = f.func_name
        return func
