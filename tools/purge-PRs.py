#!/usr/bin/env python
# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import argparse

from getpass import getpass

from github import Github


p = argparse.ArgumentParser(description='Powerline release script')
p.add_argument('-u', '--user', type=str, metavar='USER', help='Github username.', required=True)
p.add_argument('-p', '--password', type=str, metavar='PASS', help='Github password. You will be prompted if it is not supplied.')

if __name__ == '__main__':
	args = p.parse_args()
	user = args.user
	password = args.password or getpass('Password for {0}: '.format(user))
	gh = Github(user, password)
	grepo = gh.get_repo('powerline/powerline')
	for pr in grepo.get_pulls():
		if pr.base.ref != 'develop':
			issue = grepo.get_issue(pr.number)
			issue.create_comment('PRs to any branch, but develop, are not accepted.', )
			issue.add_to_labels('s:invalid')
			issue.edit(state='closed')
