# -*- coding: utf-8 -*-
import os
from powerline.lib.memoize import memoize

# TODO: fix the filenames for memoize as they won't work in all situations
# (if system is Windows, if TMPDIR isn't /tmp, etc.)


def user_name():
    user_name = os.environ.get('USER')
    return {
        'contents': user_name,
        'highlight': 'user_name' if user_name != 'root' else ['user_name_root', 'user_name'],
    }


def date(fmt='%Y-%m-%d'):
    from datetime.datetime import now
    return now().strftime(fmt)


def day():
    return date('%a')


def time():
    return date('%H:%M')


@memoize(600, filename='/tmp/powerline-externalip.tmp')
def external_ip():
    import urllib2
    url = 'http://automation.whatismyip.com/n09230945.asp'
    try:
        return u'ⓦ  ' + urllib2.urlopen(url).read()
    except urllib2.HTTPError:
        return


def system_load():
    from multiprocessing import cpu_count
    averages = os.getloadavg()
    normalized = averages[1] / cpu_count()
    if normalized < 1:
        gradient = 'system_load_good'
    elif normalized < 2:
        gradient = 'system_load_bad'
    else:
        gradient = 'system_load_ugly'
    return {
        'contents': '%.1f, %.1f, %.1f' % averages,
        'highlight': [gradient, 'system_load']
    }


def uptime():
    # TODO: make this work with operating systems without /proc/uptime
    try:
        with open('/proc/uptime', 'r') as f:
            seconds = float(f.readline().split()[0])
            minutes, seconds = divmod(seconds, 60)
            hours, minutes = divmod(minutes, 60)
            days, hours = divmod(hours, 24)
            return u'⇑ %02dd%02dh%02dm' % (days, hours, minutes)
    except IOError:
        pass


@memoize(600, filename='/tmp/powerline-forecast.tmp')
def forecast(zipcode, units='f'):
    import json
    import urllib
    import urllib2
    import time

    # This is pretty verbose and could probably be improved... checking all the
    # conditions like this is pretty ugly...
    conditions = {
        u'〇': ['clear', 'fair', 'cold'],
        u'⚑': ['windy', 'fair/windy'],
        u'☔': [
            'rain', 'mixed rain and snow', 'mixed rain and sleet',
            'freezing drizzle', 'drizzle', 'freezing rain', 'showers',
            'mixed rain and hail', 'scattered showers',
            'isolated thundershowers', 'thundershowers',
            'light rain with thunder', 'light rain'
        ],
        u'☁': [
            'cloudy', 'mostly cloudy', 'partly cloudy', 'partly cloudy/windy'
        ],
        u'❅': [
            'snow', 'mixed snow and sleet', 'snow flurries',
            'light snow showers', 'blowing snow', 'sleet', 'hail',
            'heavy snow', 'snow showers', 'scattered snow showers',
            'light snow'
        ],
        u'☈': [
            'tornado', 'tropical storm', 'hurricane', 'severe thunderstorms',
            'thunderstorms', 'isolated thunderstorms',
            'scattered thunderstorms'
        ],
        u'〰': ['dust', 'foggy', 'fog', 'haze', 'smoky', 'blustery', 'mist'],
        u'☼': ['sunny', 'hot'],
    }
    data = {
        'q': ('select item from weather.forecast where '
              'location="{0}" and u="{1}"'.format(zipcode, units)),
        'format': 'json'
    }
    url = 'http://query.yahooapis.com/v1/public/yql?' + urllib.urlencode(data)
    try:
        response = json.loads(urllib2.urlopen(url).read())
    except urllib2.HTTPError:
        return
    condition = response['query']['results']['channel']['item']['condition']
    text = condition['text'].lower()
    hour = time.localtime().tm_hour
    icon = u'〇'

    if hour > 22 or hour < 5 and (text in conditions[u'〇'] or
                                  text in conditions[u'☼']):
        icon = u'☾'
    else:
        for key, matches in conditions.items():
            if text in matches:
                icon = key
                break

    return u'{0} {1}°{2}'.format(icon, condition['temp'], units.upper())
