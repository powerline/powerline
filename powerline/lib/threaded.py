# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

from threading import Thread, Lock, Event
from types import MethodType

from powerline.lib.monotonic import monotonic
from powerline.segments import Segment


class MultiRunnedThread(object):
	daemon = True

	def __init__(self):
		self.thread = None

	def is_alive(self):
		return self.thread and self.thread.is_alive()

	def start(self):
		self.shutdown_event.clear()
		self.thread = Thread(target=self.run)
		self.thread.daemon = self.daemon
		self.thread.start()

	def join(self, *args, **kwargs):
		if self.thread:
			return self.thread.join(*args, **kwargs)
		return None


class ThreadedSegment(Segment, MultiRunnedThread):
	min_sleep_time = 0.1
	update_first = True
	interval = 1
	daemon = False

	argmethods = ('render', 'set_state')

	def __init__(self):
		super(ThreadedSegment, self).__init__()
		self.run_once = True
		self.crashed = False
		self.crashed_value = None
		self.update_value = None
		self.updated = False

	def __call__(self, pl, update_first=True, **kwargs):
		if self.run_once:
			self.pl = pl
			self.set_state(**kwargs)
			update_value = self.get_update_value(True)
		elif not self.is_alive():
			# Without this we will not have to wait long until receiving bug “I 
			# opened vim, but branch information is only shown after I move 
			# cursor”.
			#
			# If running once .update() is called in __call__.
			self.start()
			update_value = self.get_update_value(self.do_update_first)
		else:
			update_value = self.get_update_value(not self.updated)

		if self.crashed:
			return self.crashed_value

		return self.render(update_value, update_first=update_first, pl=pl, **kwargs)

	def set_update_value(self):
		try:
			self.update_value = self.update(self.update_value)
		except Exception as e:
			self.exception('Exception while updating: {0}', str(e))
			self.crashed = True
		except KeyboardInterrupt:
			self.warn('Caught keyboard interrupt while updating')
			self.crashed = True
		else:
			self.crashed = False
			self.updated = True

	def get_update_value(self, update=False):
		if update:
			self.set_update_value()
		return self.update_value

	def run(self):
		if self.do_update_first:
			start_time = monotonic()
			while True:
				self.shutdown_event.wait(max(self.interval - (monotonic() - start_time), self.min_sleep_time))
				if self.shutdown_event.is_set():
					break
				start_time = monotonic()
				self.set_update_value()
		else:
			while not self.shutdown_event.is_set():
				start_time = monotonic()
				self.set_update_value()
				self.shutdown_event.wait(max(self.interval - (monotonic() - start_time), self.min_sleep_time))

	def shutdown(self):
		self.shutdown_event.set()
		if self.daemon and self.is_alive():
			# Give the worker thread a chance to shutdown, but don’t block for 
			# too long
			self.join(0.01)

	def set_interval(self, interval=None):
		# Allowing “interval” keyword in configuration.
		# Note: Here **kwargs is needed to support foreign data, in subclasses 
		# it can be seen in a number of places in order to support 
		# .set_interval().
		interval = interval or getattr(self, 'interval')
		self.interval = interval

	def set_state(self, interval=None, update_first=True, shutdown_event=None, **kwargs):
		self.set_interval(interval)
		self.shutdown_event = shutdown_event or Event()
		self.do_update_first = update_first and self.update_first
		self.updated = self.updated or (not self.do_update_first)

	def startup(self, pl, **kwargs):
		self.run_once = False
		self.pl = pl
		self.daemon = pl.use_daemon_threads

		self.set_state(**kwargs)

		if not self.is_alive():
			self.start()

	def critical(self, *args, **kwargs):
		self.pl.critical(prefix=self.__class__.__name__, *args, **kwargs)

	def exception(self, *args, **kwargs):
		self.pl.exception(prefix=self.__class__.__name__, *args, **kwargs)

	def info(self, *args, **kwargs):
		self.pl.info(prefix=self.__class__.__name__, *args, **kwargs)

	def error(self, *args, **kwargs):
		self.pl.error(prefix=self.__class__.__name__, *args, **kwargs)

	def warn(self, *args, **kwargs):
		self.pl.warn(prefix=self.__class__.__name__, *args, **kwargs)

	def debug(self, *args, **kwargs):
		self.pl.debug(prefix=self.__class__.__name__, *args, **kwargs)

	def argspecobjs(self):
		for name in self.argmethods:
			try:
				yield name, getattr(self, name)
			except AttributeError:
				pass

	def additional_args(self):
		return (('interval', self.interval),)

	def omitted_args(self, name, method):
		if isinstance(getattr(self, name, None), MethodType):
			omitted_indexes = (0,)
		else:
			omitted_indexes = ()
		if name.startswith('render'):
			if omitted_indexes:
				omitted_indexes += (1,)
			else:
				omitted_indexes = (0,)
		return omitted_indexes


class KwThreadedSegment(ThreadedSegment):
	update_first = True

	argmethods = ('render', 'set_state', 'key', 'render_one')

	def __init__(self):
		super(KwThreadedSegment, self).__init__()
		self.updated = True
		self.update_value = ({}, set())
		self.write_lock = Lock()
		self.new_queries = []

	@staticmethod
	def key(**kwargs):
		return frozenset(kwargs.items())

	def render(self, update_value, update_first, key=None, after_update=False, **kwargs):
		queries, crashed = update_value
		if key is None:
			key = self.key(**kwargs)
		if key in crashed:
			return self.crashed_value

		try:
			update_state = queries[key][1]
		except KeyError:
			with self.write_lock:
				self.new_queries.append(key)
			if self.do_update_first or self.run_once:
				if after_update:
					self.error('internal error: value was not computed even though update_first was set')
					update_state = None
				else:
					return self.render(
						update_value=self.get_update_value(True),
						update_first=False,
						key=key,
						after_update=True,
						**kwargs
					)
			else:
				update_state = None

		return self.render_one(update_state, **kwargs)

	def update_one(self, crashed, updates, key):
		try:
			updates[key] = (monotonic(), self.compute_state(key))
		except Exception as e:
			self.exception('Exception while computing state for {0!r}: {1}', key, str(e))
			crashed.add(key)
		except KeyboardInterrupt:
			self.warn('Interrupt while computing state for {0!r}', key)
			crashed.add(key)

	def update(self, old_update_value):
		updates = {}
		crashed = set()
		update_value = (updates, crashed)
		queries = old_update_value[0]

		new_queries = self.new_queries
		with self.write_lock:
			self.new_queries = []

		for key, (last_query_time, state) in queries.items():
			if last_query_time < monotonic() < last_query_time + self.interval:
				updates[key] = (last_query_time, state)
			else:
				self.update_one(crashed, updates, key)

		for key in new_queries:
			self.update_one(crashed, updates, key)

		return update_value

	def set_state(self, interval=None, update_first=True, shutdown_event=None, **kwargs):
		self.set_interval(interval)
		self.do_update_first = update_first and self.update_first
		self.shutdown_event = shutdown_event or Event()

	@staticmethod
	def render_one(update_state, **kwargs):
		return update_state
