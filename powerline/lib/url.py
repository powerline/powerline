# -*- coding: utf-8 -*-


def urllib_read(url):
	try:
		import urllib.error
		import urllib.request
		try:
			return urllib.request.urlopen(url, timeout=5).read().decode('utf-8')
		except:
			return
	except ImportError:
		import urllib2
		try:
			return urllib2.urlopen(url, timeout=5).read()
		except urllib2.HTTPError:
			return


def urllib_urlencode(string):
	try:
		import urllib.parse
		return urllib.parse.urlencode(string)
	except ImportError:
		import urllib
		return urllib.urlencode(string)
