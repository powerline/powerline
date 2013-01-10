# -*- coding: utf-8 -*-

import time
import shelve


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

        if self.filename:
            self.caches = shelve.open(self.filename)

        def func(*args, **kwargs):
            key = (args, tuple(kwargs.items().sort()))
            if self.additional_key:
                key += (self.additional_key(), )
            result = self.caches.get(key, None)
            if result is None or time.time() - result[1] > self.timeout:
                result = self.caches[key] = f(*args, **kwargs), time.time()
                if self.filename:
                    self.caches.close()
            return result[0]

        func.func_name = f.func_name
        return func
