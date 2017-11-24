# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import os
import sys
import re

from powerline.lib.shell import run_cmd


def _fetch_battery_info(pl):
	try:
		import dbus
	except ImportError:
		pl.debug('Not using DBUS+UPower as dbus is not available')
	else:
		try:
			bus = dbus.SystemBus()
		except Exception as e:
			pl.exception('Failed to connect to system bus: {0}', str(e))
		else:
			interface = 'org.freedesktop.UPower'
			try:
				up = bus.get_object(interface, '/org/freedesktop/UPower')
			except dbus.exceptions.DBusException as e:
				if getattr(e, '_dbus_error_name', '').endswith('ServiceUnknown'):
					pl.debug('Not using DBUS+UPower as UPower is not available via dbus')
				else:
					pl.exception('Failed to get UPower service with dbus: {0}', str(e))
			else:
				devinterface = 'org.freedesktop.DBus.Properties'
				devtype_name = interface + '.Device'
				devices = []
				for devpath in up.EnumerateDevices(dbus_interface=interface):
					dev = bus.get_object(interface, devpath)
					devget = lambda what: dev.Get(
						devtype_name,
						what,
						dbus_interface=devinterface
					)
					if int(devget('Type')) != 2:
						pl.debug('Not using DBUS+UPower with {0}: invalid type', devpath)
						continue
					if not bool(devget('IsPresent')):
						pl.debug('Not using DBUS+UPower with {0}: not present', devpath)
						continue
					if not bool(devget('PowerSupply')):
						pl.debug('Not using DBUS+UPower with {0}: not a power supply', devpath)
						continue
					devices.append(devpath)
					pl.debug('Using DBUS+UPower with {0}', devpath)
				if devices:
					def _flatten_battery(pl):
						energy = 0.0
						energy_full = 0.0
						state = True
						for devpath in devices:
							dev = bus.get_object(interface, devpath)
							energy_full += float(
								dbus.Interface(dev, dbus_interface=devinterface).Get(
									devtype_name,
									'EnergyFull'
								),
							)
							energy += float(
								dbus.Interface(dev, dbus_interface=devinterface).Get(
									devtype_name,
									'Energy'
								),
							)
							state &= dbus.Interface(dev, dbus_interface=devinterface).Get(
								devtype_name,
								'State'
							) != 2
						if energy_full > 0:
							return (energy * 100.0 / energy_full), state
						else:
							return 0.0, state
					return _flatten_battery
				pl.debug('Not using DBUS+UPower as no batteries were found')

	if os.path.isdir('/sys/class/power_supply'):
		# ENERGY_* attributes represents capacity in µWh only.
		# CHARGE_* attributes represents capacity in µAh only.
		linux_capacity_units = ('energy', 'charge')
		linux_energy_full_fmt = '/sys/class/power_supply/{0}/{1}_full'
		linux_energy_fmt = '/sys/class/power_supply/{0}/{1}_now'
		linux_status_fmt = '/sys/class/power_supply/{0}/status'
		devices = []
		for linux_supplier in os.listdir('/sys/class/power_supply'):
			for unit in linux_capacity_units:
				energy_path = linux_energy_fmt.format(linux_supplier, unit)
				if not os.path.exists(energy_path):
					continue
				pl.debug('Using /sys/class/power_supply with battery {0} and unit {1}',
					linux_supplier, unit)
				devices.append((linux_supplier, unit))
				break  # energy or charge, not both
		if devices:
			def _get_battery_status(pl):
				energy = 0.0
				energy_full = 0.0
				state = True
				for device, unit in devices:
					with open(linux_energy_full_fmt.format(device, unit), 'r') as f:
						energy_full += int(float(f.readline().split()[0]))
					with open(linux_energy_fmt.format(device, unit), 'r') as f:
						energy += int(float(f.readline().split()[0]))
					try:
						with open(linux_status_fmt.format(device), 'r') as f:
							state &= (f.readline().strip() != 'Discharging')
					except IOError:
						state = None
				return (energy * 100.0 / energy_full), state
			return _get_battery_status
			pl.debug('Not using /sys/class/power_supply as no batteries were found')
		else:
			pl.debug("Checking for first capacity battery percentage")
			for batt in os.listdir('/sys/class/power_supply'):
				if os.path.exists('/sys/class/power_supply/{0}/capacity'.format(batt)):
					def _get_battery_perc(pl):
						state = True
						with open('/sys/class/power_supply/{0}/capacity'.format(batt), 'r') as f:
							perc = int(f.readline().split()[0])
						try:
							with open(linux_status_fmt.format(batt), 'r') as f:
								state &= (f.readline().strip() != 'Discharging')
						except IOError:
							state = None
						return perc, state
					return _get_battery_perc
	else:
		pl.debug('Not using /sys/class/power_supply: no directory')

	try:
		from shutil import which  # Python-3.3 and later
	except ImportError:
		pl.info('Using dumb “which” which only checks for file in /usr/bin')
		which = lambda f: (lambda fp: os.path.exists(fp) and fp)(os.path.join('/usr/bin', f))

	if which('pmset'):
		pl.debug('Using pmset')

		BATTERY_PERCENT_RE = re.compile(r'(\d+)%')

		def _get_battery_status(pl):
			battery_summary = run_cmd(pl, ['pmset', '-g', 'batt'])
			battery_percent = BATTERY_PERCENT_RE.search(battery_summary).group(1)
			ac_charging = 'AC' in battery_summary
			return int(battery_percent), ac_charging
		return _get_battery_status
	else:
		pl.debug('Not using pmset: executable not found')

	if sys.platform.startswith('win') or sys.platform == 'cygwin':
		# From http://stackoverflow.com/a/21083571/273566, reworked
		try:
			from win32com.client import GetObject
		except ImportError:
			pl.debug('Not using win32com.client as it is not available')
		else:
			try:
				wmi = GetObject('winmgmts:')
			except Exception as e:
				pl.exception('Failed to run GetObject from win32com.client: {0}', str(e))
			else:
				for battery in wmi.InstancesOf('Win32_Battery'):
					pl.debug('Using win32com.client with Win32_Battery')

					def _get_battery_status(pl):
						# http://msdn.microsoft.com/en-us/library/aa394074(v=vs.85).aspx
						return battery.EstimatedChargeRemaining, battery.BatteryStatus == 6

					return _get_battery_status
				pl.debug('Not using win32com.client as no batteries were found')
		from ctypes import Structure, c_byte, c_ulong, byref
		if sys.platform == 'cygwin':
			pl.debug('Using cdll to communicate with kernel32 (Cygwin)')
			from ctypes import cdll
			library_loader = cdll
		else:
			pl.debug('Using windll to communicate with kernel32 (Windows)')
			from ctypes import windll
			library_loader = windll

		class PowerClass(Structure):
			_fields_ = [
				('ACLineStatus', c_byte),
				('BatteryFlag', c_byte),
				('BatteryLifePercent', c_byte),
				('Reserved1', c_byte),
				('BatteryLifeTime', c_ulong),
				('BatteryFullLifeTime', c_ulong)
			]

		def _get_battery_status(pl):
			powerclass = PowerClass()
			result = library_loader.kernel32.GetSystemPowerStatus(byref(powerclass))
			# http://msdn.microsoft.com/en-us/library/windows/desktop/aa372693(v=vs.85).aspx
			if result:
				return None
			return powerclass.BatteryLifePercent, powerclass.ACLineStatus == 1

		if _get_battery_status() is None:
			pl.debug('Not using GetSystemPowerStatus because it failed')
		else:
			pl.debug('Using GetSystemPowerStatus')

		return _get_battery_status

	raise NotImplementedError


def _get_battery_status(pl):
	global _get_battery_status

	def _failing_get_status(pl):
		raise NotImplementedError

	try:
		_get_battery_status = _fetch_battery_info(pl)
	except NotImplementedError:
		_get_battery_status = _failing_get_status
	except Exception as e:
		pl.exception('Exception while obtaining battery status: {0}', str(e))
		_get_battery_status = _failing_get_status
	return _get_battery_status(pl)


def battery(pl, format='{ac_state} {capacity:3.0%}', steps=5, gamify=False, full_heart='O', empty_heart='O', online='C', offline=' '):
	'''Return battery charge status.

	:param str format:
		Percent format in case gamify is False. Format arguments: ``ac_state`` 
		which is equal to either ``online`` or ``offline`` string arguments and 
		``capacity`` which is equal to current battery capacity in interval [0, 
		100].
	:param int steps:
		Number of discrete steps to show between 0% and 100% capacity if gamify
		is True.
	:param bool gamify:
		Measure in hearts (♥) instead of percentages. For full hearts 
		``battery_full`` highlighting group is preferred, for empty hearts there 
		is ``battery_empty``. ``battery_online`` or ``battery_offline`` group 
		will be used for leading segment containing ``online`` or ``offline`` 
		argument contents.
	:param str full_heart:
		Heart displayed for “full” part of battery.
	:param str empty_heart:
		Heart displayed for “used” part of battery. It is also displayed using
		another gradient level and highlighting group, so it is OK for it to be 
		the same as full_heart as long as necessary highlighting groups are 
		defined.
	:param str online:
		Symbol used if computer is connected to a power supply.
	:param str offline:
		Symbol used if computer is not connected to a power supply.

	``battery_gradient`` and ``battery`` groups are used in any case, first is 
	preferred.

	Highlight groups used: ``battery_full`` or ``battery_gradient`` (gradient) or ``battery``, ``battery_empty`` or ``battery_gradient`` (gradient) or ``battery``, ``battery_online`` or ``battery_ac_state`` or ``battery_gradient`` (gradient) or ``battery``, ``battery_offline`` or ``battery_ac_state`` or ``battery_gradient`` (gradient) or ``battery``.
	'''
	try:
		capacity, ac_powered = _get_battery_status(pl)
	except NotImplementedError:
		pl.info('Unable to get battery status.')
		return None

	ret = []
	if gamify:
		denom = int(steps)
		numer = int(denom * capacity / 100)
		ret.append({
			'contents': online if ac_powered else offline,
			'draw_inner_divider': False,
			'highlight_groups': ['battery_online' if ac_powered else 'battery_offline', 'battery_ac_state', 'battery_gradient', 'battery'],
			'gradient_level': 0,
		})
		ret.append({
			'contents': full_heart * numer,
			'draw_inner_divider': False,
			'highlight_groups': ['battery_full', 'battery_gradient', 'battery'],
			# Using zero as “nothing to worry about”: it is least alert color.
			'gradient_level': 0,
		})
		ret.append({
			'contents': empty_heart * (denom - numer),
			'draw_inner_divider': False,
			'highlight_groups': ['battery_empty', 'battery_gradient', 'battery'],
			# Using a hundred as it is most alert color.
			'gradient_level': 100,
		})
	else:
		ret.append({
			'contents': format.format(ac_state=(online if ac_powered else offline), capacity=(capacity / 100.0)),
			'highlight_groups': ['battery_gradient', 'battery'],
			# Gradients are “least alert – most alert” by default, capacity has 
			# the opposite semantics.
			'gradient_level': 100 - capacity,
		})
	return ret
