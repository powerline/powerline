# -*- coding: utf-8 -*-

import os


def user_name():
	user_name = os.environ.get('USER')
	return {
		'contents': user_name,
		'highlight': 'user_name' if user_name != 'root' else ['user_name_root', 'user_name'],
	}
