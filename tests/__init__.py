# vim:fileencoding=utf-8:noet
import sys
if sys.version_info < (2, 7):
	from unittest2 import TestCase, main  # NOQA
else:
	from unittest import TestCase, main  # NOQA

# multiprocessing registers an exit handler that raises exceptions which get
# printed to stdout, looking ugly. Since we only use cpu_count from
# multiprocessing we dont need its idiotic exit handler
import atexit
if hasattr(atexit, '_exithandlers'):
	import multiprocessing
	atexit._exithandlers.pop()
else:
	from multiprocessing.util import _exit_function
	atexit.unregister(_exit_function)
