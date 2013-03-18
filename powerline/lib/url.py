# vim:fileencoding=utf-8:noet

try:
	from urllib.error import HTTPError
	from urllib.request import urlopen
	from urllib.parse import urlencode as urllib_urlencode  # NOQA
except ImportError:
	from urllib2 import urlopen, HTTPError  # NOQA
	from urllib import urlencode as urllib_urlencode  # NOQA


def urllib_read(url):
	try:
		return urlopen(url, timeout=10).read().decode('utf-8')
	except HTTPError:
		return
