# vim:fileencoding=utf-8:noet

from __future__ import absolute_import

from powerline.lib.time import monotonic

from time import sleep
from threading import Thread, Lock


class ThreadedSegment(Thread):
	daemon = True
	min_sleep_time = 0.1

	def __init__(self):
		super(ThreadedSegment, self).__init__()
		self.update_lock = Lock()
		self.write_lock = Lock()
		self.keep_going = True
		self.run_once = True
		self.did_set_interval = False

	def __call__(self, **kwargs):
		if self.run_once:
			self.set_state(**kwargs)
			self.update()
		elif not self.is_alive():
			self.startup(**kwargs)

		with self.write_lock:
			return self.render(**kwargs)

	def sleep(self, adjust_time):
		sleep(max(self.interval - adjust_time, self.min_sleep_time))

	def run(self):
		while self.keep_going:
			start_time = monotonic()

			with self.update_lock:
				self.update()

			self.sleep(monotonic() - start_time)

	def shutdown(self):
		self.keep_going = False

	def set_interval(self, interval=None, **kwargs):
		# Allowing “interval” keyword in configuration.
		# Note: Here **kwargs is needed to support foreign data, in subclasses 
		# it can be seen in a number of places in order to support 
		# .set_interval().
		interval = interval or getattr(self, 'interval', 1)
		self.interval = interval
		self.has_set_interval = True

	def set_state(self, **kwargs):
		if not self.did_set_interval:
			self.set_interval(**kwargs)

	def startup(self, **kwargs):
		# Normally .update() succeeds to run before value is requested, meaning 
		# that user is getting values he needs directly at vim startup. Without 
		# .startup() we will not have to wait long until receiving bug “I opened 
		# vim, but branch information is only shown after I move cursor”.
		self.run_once = False

		self.set_state(**kwargs)

		if not self.is_alive():
			self.start()


def printed(func):
	def f(*args, **kwargs):
		print(func.__name__)
		return func(*args, **kwargs)
	return f


class KwThreadedSegment(ThreadedSegment):
	drop_interval = 10 * 60

	def __init__(self):
		super(KwThreadedSegment, self).__init__()
		self.queries = {}
		self.update_missing = True

	@staticmethod
	def key(**kwargs):
		return frozenset(kwargs.items())

	def render(self, **kwargs):
		key = self.key(**kwargs)
		try:
			update_state = self.queries[key][1]
		except KeyError:
			update_state = self.compute_state(key) if self.update_missing else None
		# No locks: render method is already running with write_lock acquired.
		self.queries[key] = (monotonic(), update_state)
		return self.render_one(update_state, **kwargs)

	def update(self):
		updates = {}
		removes = []
		for key, (last_query_time, state) in list(self.queries.items()):
			if last_query_time < monotonic() < last_query_time + self.drop_interval:
				updates[key] = (last_query_time, self.compute_state(key))
			else:
				removes.append(key)
		with self.write_lock:
			self.queries.update(updates)
			for key in removes:
				self.queries.pop(key)

	def set_state(self, **kwargs):
		if not self.did_set_interval or ('interval' in kwargs and self.interval > kwargs['interval']):
			self.set_interval(**kwargs)

		key = self.key(**kwargs)
		self.queries[key] = (monotonic(), None)

	@staticmethod
	def render_one(update_state, **kwargs):
		return update_state


def with_docstring(instance, doc):
	instance.__doc__ = doc
	return instance
