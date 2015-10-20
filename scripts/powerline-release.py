#!/usr/bin/env python
# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import argparse
import codecs
import os
import re

from subprocess import check_output, check_call, CalledProcessError
from getpass import getpass

from github import Github


OVERLAY_NAME = 'raiagent'
OVERLAY = 'leycec/' + OVERLAY_NAME
OVERLAY_BRANCH_FORMAT = 'powerline-release-{0}'


def parse_version(s):
	if s == ('+' * len(s)):
		try:
			last_version = next(iter(sorted([
				tuple(map(int, tag.split('.')))
				for tag in check_output(['git', 'tag', '-l', '[0-9]*.*']).split('\n')[:-1]
			], reverse=True)))
		except StopIteration:
			raise ValueError('No existing versions found')

		version = []
		for i in range(len(s) - 1):
			try:
				version.append(last_version[i])
			except IndexError:
				version.append(0)

		try:
			version.append(last_version[len(s) - 1] + 1)
		except IndexError:
			version.append(1)

		if len(version) == 1:
			version.append(0)

		return tuple(version)
	else:
		return tuple(map(int, s.split('.')))


def setup_py_filter(filter_func):
	with codecs.open('.setup.py.new', 'w', encoding='utf-8') as NS:
		with codecs.open('setup.py', 'r', encoding='utf-8') as OS:
			for line in OS:
				line = filter_func(line)
				NS.write(line)

	os.unlink('setup.py')
	os.rename('.setup.py.new', 'setup.py')


def setup_py_develop_filter(line, version_string):
	if line.startswith('\tbase_version = '):
		line = '\tbase_version = \'' + version_string + '\'\n'
	return line


def setup_py_master_filter(line, version_string):
	if line.startswith('\tversion='):
		line = '\tversion=\'' + version_string + '\',\n'
	elif 'Development Status' in line:
		line = '\t\t\'Development Status :: 5 - Production/Stable\',\n'
	return line


def merge(version_string, rev, **kwargs):
	check_call(['git', 'checkout', rev])

	temp_branch_name = 'release-' + version_string
	check_call(['git', 'checkout', '-b', temp_branch_name])
	setup_py_filter(lambda line: setup_py_develop_filter(line, version_string))
	check_call(['git', 'add', 'setup.py'])
	check_call(['git', 'commit', '-m', 'Update base version'])
	check_call(['git', 'checkout', rev])
	check_call(['git', 'merge', '--no-ff',
	                            '--strategy', 'recursive',
	                            '--strategy-option', 'theirs',
	                            '--commit',
	                            '-m', 'Merge branch \'{0}\' into {1}'.format(temp_branch_name, rev),
	                            temp_branch_name])
	check_call(['git', 'branch', '-d', temp_branch_name])

	rev = check_output(['git', 'rev-parse', 'HEAD']).strip()

	check_call(['git', 'checkout', 'master'])
	try:
		check_call(['git', 'merge', '--no-ff', '--no-commit', '--log', rev])
	except CalledProcessError:
		check_call(['git', 'mergetool', '--tool', 'vimdiff2'])

	setup_py_filter(lambda line: setup_py_master_filter(line, version_string))
	check_call(['git', 'add', 'setup.py'])

	check_call(['git', 'commit'])
	check_call(['git', 'tag', '-m', 'Release ' + version_string, '-a', version_string])


def push(version_string, rev, **kwargs):
	check_call(['git', 'push', 'upstream', 'master'])
	check_call(['git', 'push', 'upstream', version_string])
	check_call(['git', 'push', 'upstream', rev])


def upload(**args):
	check_call(['python', 'setup.py', 'sdist', 'upload'])
	check_call(['python', 'setup.py', 'upload_docs'])


gh = None


def get_gh(user, password):
	global gh
	if not gh:
		gh = Github(user, password)
	return gh


def create_ebuilds(version_string, overlay, user, **kwargs):
	overlay_url = 'git://github.com/' + OVERLAY
	if not os.path.isdir(overlay):
		check_call(['git', 'clone', overlay_url, overlay])
	check_call(['git', 'checkout', 'master'], cwd=overlay)
	check_call(['git', 'pull', '--ff-only', overlay_url, 'master'], cwd=overlay)
	branch = OVERLAY_BRANCH_FORMAT.format(version_string)
	check_call(['git', 'branch', branch], cwd=overlay)
	check_call(['git', 'checkout', branch], cwd=overlay)
	os.environ['DISTDIR'] = '/tmp/powerline-distfiles'
	if not os.path.isdir(os.environ['DISTDIR']):
		os.mkdir(os.environ['DISTDIR'])
	new_files = []
	for category, pn in (
		('app-misc', 'powerline'),
		('app-vim', 'powerline-vim'),
	):
		pdir = os.path.join(overlay, category, pn)
		live_ebuild = None
		for ebuild in os.listdir(pdir):
			if ebuild.endswith('.ebuild') and '9999' in ebuild:
				live_ebuild_base = ebuild
				live_ebuild = os.path.join(pdir, ebuild)
				break
		assert(live_ebuild)
		vcur = os.path.join(pdir, '{0}-{1}.ebuild'.format(pn, version_string))
		if pn == 'powerline-vim':
			with open(live_ebuild) as LEF:
				with open(vcur, 'w') as F:
					dropnext = False
					for line in LEF:
						if line.startswith('EGIT'):
							# Drop all EGIT_… and the next empty line
							dropnext = True
							next_re = re.compile('^$')
							continue
						if dropnext:
							assert(next_re.match(line))
							dropnext = False
							continue
						if line.startswith('# Note the lack of an assignment to ${S}'):
							next_re = re.compile('^#')
							dropnext = True
							line = 'S="${WORKDIR}/${MY_P}"\n'
						if line.startswith('inherit'):
							line = line.replace(' git-r3', '')
							line += '\n'
							line += 'MY_PN="powerline-status"\n'
							line += 'MY_P="${MY_PN}-${PV}"'
							line += '\n'
						elif line.startswith('HOMEPAGE'):
							line += 'SRC_URI="mirror://pypi/p/${MY_PN}/${MY_P}.tar.gz"\n'
						elif line.startswith('KEYWORDS'):
							line = 'KEYWORDS="~amd64 ~ppc ~x86 ~x86-fbsd"\n'
						F.write(line)
		else:
			os.symlink(live_ebuild_base, vcur)
		new_files.append(vcur)
		check_call(['ebuild', vcur, 'manifest'])
		new_files.append(os.path.join(pdir, 'Manifest'))
	check_call(['git', 'add', '--'] + new_files, cwd=overlay)
	check_call(['git', 'commit'] + new_files + ['-m', 'powerline*: Release {0}'.format(version_string)],
	           cwd=overlay)
	check_call(['git', 'push', '-f', 'git@github.com:{0}/{1}'.format(user, OVERLAY_NAME), branch], cwd=overlay)


def update_overlay(version_string, user, password, **kwargs):
	gh = get_gh(user, password)
	overlay = gh.get_repo(OVERLAY)
	overlay.create_pull(
		title='New powerline version: ' + version_string,
		body='Add ebuilds for new powerline version\n\n---\n\nCreated automatically by release script',
		base='master',
		head=user + ':' + OVERLAY_BRANCH_FORMAT.format(version_string),
	)


stages = (
	('merge', merge),
	('push', push),
	('upload', upload),
	('create_ebuilds', create_ebuilds),
	('update_overlay', update_overlay),
)


def create_release(version, user, password=None, run_stages=None, **kwargs):
	version_string = '.'.join((str(v) for v in version))
	if not password:
		password = getpass('Password for {0}: '.format(user))
	for stname, stfunc in stages:
		if run_stages is None or stname in run_stages:
			stfunc(version_string=version_string, user=user, password=password, **kwargs)


p = argparse.ArgumentParser(description='Powerline release script')
p.add_argument('-u', '--user', type=str, metavar='USER', help='Github username.', required=True)
p.add_argument('-v', '--version', type=parse_version, metavar='VERSION', help='Use given version for the release. If version contains only `+\' signs then it will increase latest version number: one `+\' increases major version number (e.g. 1.2.3 -> 2.0), `++\' increases minor version number (e.g. 1.2.3 -> 1.3), `+++\' increases patch level (e.g. 1.2.3 -> 1.2.4). Defaults to `+++\'.', default='+++')
p.add_argument('-r', '--rev', metavar='COMMIT', help='Use given revision for the release. Defaults to `develop\'.', default='develop')
p.add_argument('-s', '--stages', action='append', metavar='STAGE', help='Only run one of the given stages (default to all).', choices=tuple((stname for stname, stfunc in stages)))
p.add_argument('-p', '--password', type=str, metavar='PASS', help='Github password. You will be prompted if it is not supplied.')
p.add_argument('-o', '--overlay', type=str, metavar='PATH', help='Location of the local clone of the {0} overlay. If provided directory does not exist it will be created by “git clone”. Defaults to /tmp/powerline-{0}.'.format(OVERLAY_NAME), default='/tmp/powerline-' + OVERLAY_NAME)


if __name__ == '__main__':
	args = p.parse_args()
	create_release(
		version=args.version,
		rev=args.rev,
		user=args.user,
		password=args.password,
		overlay=args.overlay,
		run_stages=args.stages,
	)
