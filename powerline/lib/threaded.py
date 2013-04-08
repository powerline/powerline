# vim:fileencoding=utf-8:noet

from __future__ import absolute_import

from powerline.lib.monotonic import monotonic

from threading import Thread, Lock, Event


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


class ThreadedSegment(MultiRunnedThread):
	min_sleep_time = 0.1
	update_first = True
	interval = 1
	daemon = False

	def __init__(self):
		super(ThreadedSegment, self).__init__()
		self.run_once = True
		self.skip = False
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
			update_value = self.get_update_value(update_first and self.update_first)
			self.start()
		elif not self.updated:
			update_value = self.get_update_value(True)
			self.updated = True
		else:
			update_value = self.update_value

		if self.skip:
			return self.crashed_value

		return self.render(update_value, update_first=update_first, pl=pl, **kwargs)

	def get_update_value(self, update=False):
		if update:
			self.update_value = self.update(self.update_value)
		return self.update_value

	def run(self):
		while not self.shutdown_event.is_set():
			start_time = monotonic()
			try:
				self.update_value = self.update(self.update_value)
			except Exception as e:
				self.exception('Exception while updating: {0}', str(e))
				self.skip = True
			except KeyboardInterrupt:
				self.warn('Caught keyboard interrupt while updating')
				self.skip = True
			else:
				self.skip = False
			self.shutdown_event.wait(max(self.interval - (monotonic() - start_time), self.min_sleep_time))

	def shutdown(self):
		self.shutdown_event.set()
		if self.daemon and self.is_alive():
			# Give the worker thread a chance to shutdown, but don't block for 
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
		self.updated = self.updated or (not (update_first and self.update_first))

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


class KwThreadedSegment(ThreadedSegment):
	drop_interval = 10 * 60
	update_first = True

	def __init__(self):
		super(KwThreadedSegment, self).__init__()
		self.updated = True
		self.update_value = ({}, set())
		self.write_lock = Lock()
		self.new_queries = {}

	@staticmethod
	def key(**kwargs):
		return frozenset(kwargs.items())

	def render(self, update_value, update_first, **kwargs):
		queries, crashed = update_value
		key = self.key(**kwargs)
		if key in crashed:
			return self.crashed_value

		try:
			update_state = queries[key][1]
		except KeyError:
			# Allow only to forbid to compute missing values: in either user 
			# configuration or in subclasses.
			update_state = self.compute_state(key) if ((update_first and self.update_first) or self.run_once) else None

		with self.write_lock:
			self.new_queries[key] = (monotonic(), update_state)
		return self.render_one(update_state, **kwargs)

	def update(self, old_update_value):
		updates = {}
		crashed = set()
		update_value = (updates, crashed)
		queries = old_update_value[0]
		with self.write_lock:
			if self.new_queries:
				queries.update(self.new_queries)
				self.new_queries.clear()

		for key, (last_query_time, state) in queries.items():
			if last_query_time < monotonic() < last_query_time + self.drop_interval:
				try:
					updates[key] = (last_query_time, self.compute_state(key))
				except Exception as e:
					self.exception('Exception while computing state for {0!r}: {1}', key, str(e))
					crashed.add(key)
				except KeyboardInterrupt:
					self.warn('Interrupt while computing state for {0!r}', key)
					crashed.add(key)

		return update_value

	def set_state(self, interval=None, shutdown_event=None, **kwargs):
		self.set_interval(interval)
		self.shutdown_event = shutdown_event or Event()

	@staticmethod
	def render_one(update_state, **kwargs):
		return update_state


def with_docstring(instance, doc):
	instance.__doc__ = doc
	return instance
