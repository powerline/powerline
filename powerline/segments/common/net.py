# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import re
import os
import socket

from powerline.lib.url import urllib_read
from powerline.lib.threaded import ThreadedSegment, KwThreadedSegment
from powerline.lib.monotonic import monotonic
from powerline.lib.humanize_bytes import humanize_bytes
from powerline.segments import with_docstring
from powerline.theme import requires_segment_info


@requires_segment_info
def hostname(pl, segment_info, only_if_ssh=False, exclude_domain=False):
	'''Return the current hostname.

	:param bool only_if_ssh:
		only return the hostname if currently in an SSH session
	:param bool exclude_domain:
		return the hostname without domain if there is one
	'''
	if only_if_ssh and not segment_info['environ'].get('SSH_CLIENT'):
		return None
	if exclude_domain:
		return socket.gethostname().split('.')[0]
	return socket.gethostname()


def _external_ip(query_url='http://ipv4.icanhazip.com/'):
	return urllib_read(query_url).strip()


class ExternalIpSegment(ThreadedSegment):
	interval = 300

	def set_state(self, query_url='http://ipv4.icanhazip.com/', **kwargs):
		self.query_url = query_url
		super(ExternalIpSegment, self).set_state(**kwargs)

	def update(self, old_ip):
		return _external_ip(query_url=self.query_url)

	def render(self, ip, **kwargs):
		if not ip:
			return None
		return [{'contents': ip, 'divider_highlight_group': 'background:divider'}]


external_ip = with_docstring(ExternalIpSegment(),
'''Return external IP address.

:param str query_url:
	URI to query for IP address, should return only the IP address as a text string

	Suggested URIs:

	* http://ipv4.icanhazip.com/
	* http://ipv6.icanhazip.com/
	* http://icanhazip.com/ (returns IPv6 address if available, else IPv4)

Divider highlight group used: ``background:divider``.
''')


try:
	import netifaces
except ImportError:
	def internal_ip(pl, interface='auto', ipv=4):
		return None
else:
	_interface_starts = {
		'eth':      10,  # Regular ethernet adapters         : eth1
		'enp':      10,  # Regular ethernet adapters, Gentoo : enp2s0
		'ath':       9,  # Atheros WiFi adapters             : ath0
		'wlan':      9,  # Other WiFi adapters               : wlan1
		'wlp':       9,  # Other WiFi adapters, Gentoo       : wlp5s0
		'teredo':    1,  # miredo interface                  : teredo
		'lo':      -10,  # Loopback interface                : lo
		'docker':   -5,  # Docker bridge interface           : docker0
		'vmnet':    -5,  # VMWare bridge interface           : vmnet1
		'vboxnet':  -5,  # VirtualBox bridge interface       : vboxnet0
	}

	_interface_start_re = re.compile(r'^([a-z]+?)(\d|$)')

	def _interface_key(interface):
		match = _interface_start_re.match(interface)
		if match:
			try:
				base = _interface_starts[match.group(1)] * 100
			except KeyError:
				base = 500
			if match.group(2):
				return base - int(match.group(2))
			else:
				return base
		else:
			return 0

	def internal_ip(pl, interface='auto', ipv=4):
		if interface == 'auto':
			try:
				interface = next(iter(sorted(netifaces.interfaces(), key=_interface_key, reverse=True)))
			except StopIteration:
				pl.info('No network interfaces found')
				return None
		addrs = netifaces.ifaddresses(interface)
		try:
			return addrs[netifaces.AF_INET6 if ipv == 6 else netifaces.AF_INET][0]['addr']
		except (KeyError, IndexError):
			return None


internal_ip = with_docstring(internal_ip,
'''Return internal IP address

Requires ``netifaces`` module to work properly.

:param str interface:
	Interface on which IP will be checked. Use ``auto`` to automatically 
	detect interface. In this case interfaces with lower numbers will be 
	preferred over interfaces with similar names. Order of preference based on 
	names:

	#. ``eth`` and ``enp`` followed by number or the end of string.
	#. ``ath``, ``wlan`` and ``wlp`` followed by number or the end of string.
	#. ``teredo`` followed by number or the end of string.
	#. Any other interface that is not ``lo*``.
	#. ``lo`` followed by number or the end of string.
:param int ipv:
	4 or 6 for ipv4 and ipv6 respectively, depending on which IP address you 
	need exactly.
''')


try:
	import psutil

	def _get_bytes(interface):
		try:
			io_counters = psutil.net_io_counters(pernic=True)
		except AttributeError:
			io_counters = psutil.network_io_counters(pernic=True)
		if_io = io_counters.get(interface)
		if not if_io:
			return None
		return if_io.bytes_recv, if_io.bytes_sent

	def _get_interfaces():
		io_counters = psutil.network_io_counters(pernic=True)
		for interface, data in io_counters.items():
			if data:
				yield interface, data.bytes_recv, data.bytes_sent
except ImportError:
	def _get_bytes(interface):
		with open('/sys/class/net/{interface}/statistics/rx_bytes'.format(interface=interface), 'rb') as file_obj:
			rx = int(file_obj.read())
		with open('/sys/class/net/{interface}/statistics/tx_bytes'.format(interface=interface), 'rb') as file_obj:
			tx = int(file_obj.read())
		return (rx, tx)

	def _get_interfaces():
		for interface in os.listdir('/sys/class/net'):
			x = _get_bytes(interface)
			if x is not None:
				yield interface, x[0], x[1]


class NetworkLoadSegment(KwThreadedSegment):
	interfaces = {}
	replace_num_pat = re.compile(r'[a-zA-Z]+')

	@staticmethod
	def key(interface='auto', **kwargs):
		return interface

	def compute_state(self, interface):
		if interface == 'auto':
			proc_exists = getattr(self, 'proc_exists', None)
			if proc_exists is None:
				proc_exists = self.proc_exists = os.path.exists('/proc/net/route')
			if proc_exists:
				# Look for default interface in routing table
				with open('/proc/net/route', 'rb') as f:
					for line in f.readlines():
						parts = line.split()
						if len(parts) > 1:
							iface, destination = parts[:2]
							if not destination.replace(b'0', b''):
								interface = iface.decode('utf-8')
								break
			if interface == 'auto':
				# Choose interface with most total activity, excluding some
				# well known interface names
				interface, total = 'eth0', -1
				for name, rx, tx in _get_interfaces():
					base = self.replace_num_pat.match(name)
					if None in (base, rx, tx) or base.group() in ('lo', 'vmnet', 'sit'):
						continue
					activity = rx + tx
					if activity > total:
						total = activity
						interface = name

		try:
			idata = self.interfaces[interface]
			try:
				idata['prev'] = idata['last']
			except KeyError:
				pass
		except KeyError:
			idata = {}
			if self.run_once:
				idata['prev'] = (monotonic(), _get_bytes(interface))
				self.shutdown_event.wait(self.interval)
			self.interfaces[interface] = idata

		idata['last'] = (monotonic(), _get_bytes(interface))
		return idata.copy()

	def render_one(self, idata, recv_format='DL {value:>8}', sent_format='UL {value:>8}', suffix='B/s', si_prefix=False, **kwargs):
		if not idata or 'prev' not in idata:
			return None

		t1, b1 = idata['prev']
		t2, b2 = idata['last']
		measure_interval = t2 - t1

		if None in (b1, b2):
			return None

		r = []
		for i, key in zip((0, 1), ('recv', 'sent')):
			format = locals()[key + '_format']
			try:
				value = (b2[i] - b1[i]) / measure_interval
			except ZeroDivisionError:
				self.warn('Measure interval zero.')
				value = 0
			max_key = key + '_max'
			is_gradient = max_key in kwargs
			hl_groups = ['network_load_' + key, 'network_load']
			if is_gradient:
				hl_groups[:0] = (group + '_gradient' for group in hl_groups)
			r.append({
				'contents': format.format(value=humanize_bytes(value, suffix, si_prefix)),
				'divider_highlight_group': 'background:divider',
				'highlight_groups': hl_groups,
			})
			if is_gradient:
				max = kwargs[max_key]
				if value >= max:
					r[-1]['gradient_level'] = 100
				else:
					r[-1]['gradient_level'] = value * 100.0 / max

		return r


network_load = with_docstring(NetworkLoadSegment(),
'''Return the network load.

Uses the ``psutil`` module if available for multi-platform compatibility,
falls back to reading
:file:`/sys/class/net/{interface}/statistics/{rx,tx}_bytes`.

:param str interface:
	Network interface to measure (use the special value "auto" to have powerline 
	try to auto-detect the network interface).
:param str suffix:
	String appended to each load string.
:param bool si_prefix:
	Use SI prefix, e.g. MB instead of MiB.
:param str recv_format:
	Format string that determines how download speed should look like. Receives 
	``value`` as argument.
:param str sent_format:
	Format string that determines how upload speed should look like. Receives 
	``value`` as argument.
:param float recv_max:
	Maximum number of received bytes per second. Is only used to compute
	gradient level.
:param float sent_max:
	Maximum number of sent bytes per second. Is only used to compute gradient
	level.

Divider highlight group used: ``background:divider``.

Highlight groups used: ``network_load_sent_gradient`` (gradient) or ``network_load_recv_gradient`` (gradient) or ``network_load_gradient`` (gradient), ``network_load_sent`` or ``network_load_recv`` or ``network_load``.
''')
