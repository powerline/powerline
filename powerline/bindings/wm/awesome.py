# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

from threading import Thread, Event
from time import sleep
import dbus

from powerline import Powerline
from powerline.lib.monotonic import monotonic


def run(thread_shutdown_event=None, pl_shutdown_event=None, pl_config_loader=None,
        interval=None):
	powerline = Powerline(
		'wm',
		renderer_module='pango_markup',
		shutdown_event=pl_shutdown_event,
		config_loader=pl_config_loader,
	)
	powerline.update_renderer()

	try:
		session_bus = dbus.SessionBus()
	except Exception as e:
		powerline.pl.exception('Failed to connect to session bus: {0}', str(e))
		raise
	try:
		awesome_client = session_bus.get_object('org.naquadah.awesome.awful', '/')
	except dbus.exceptions.DBusException as e:
		powerline.pl.exception('Failed to locate Awesome service on dbus: {0}', str(e))
		raise
	awesome_eval = awesome_client.get_dbus_method('Eval', dbus_interface='org.naquadah.awesome.awful.Remote')

	if not thread_shutdown_event:
		thread_shutdown_event = powerline.shutdown_event

	while not thread_shutdown_event.is_set():
		# powerline.update_interval may change over time
		used_interval = interval or powerline.update_interval
		start_time = monotonic()
		s = powerline.render(side='right')
		request = 'powerline_widget:set_markup(\'' + s.translate({'\'': '\\\'', '\\': '\\\\'}) + '\')\n'
		try:
			awesome_eval(request.encode('utf-8'))
		except dbus.exceptions.DBusException as e:
			powerline.pl.exception('Failure while signaling Awesome on dbus: {0}', str(e))
		thread_shutdown_event.wait(max(used_interval - (monotonic() - start_time), 0.1))


class AwesomeThread(Thread):
	__slots__ = ('powerline_shutdown_event',)

	def __init__(self, **kwargs):
		super(AwesomeThread, self).__init__()
		self.powerline_run_kwargs = kwargs

	def run(self):
		run(**self.powerline_run_kwargs)
