if exists('g:powerline_loaded')
    finish
endif
let g:powerline_loaded = 1

if exists('g:powerline_pycmd')
	let s:pycmd = substitute(g:powerline_pycmd, '\v\C^(py)%[thon](3?)$', '\1\2', '')
	if s:pycmd is# 'py'
		let s:has_python = has('python')
		let s:pyeval = get(g:, 'powerline_pyeval', 'pyeval')
	elseif s:pycmd is# 'py3'
		let s:has_python = has('python3')
		let s:pyeval = 'py3eval'
		let s:pyeval = get(g:, 'powerline_pyeval', 'py3eval')
	else
		if !exists('g:powerline_pyeval')
			echohl ErrorMsg
				echomsg 'g:powerline_pycmd was set to an unknown values, but g:powerline_pyeval'
				echomsg 'was not set. You should either set g:powerline_pycmd to "py3" or "py",'
				echomsg 'specify g:powerline_pyeval explicitly or unset both and let powerline'
				echomsg 'figure them out.'
			echohl None
			unlet s:pycmd
			finish
		endif
		let s:pyeval = g:powerline_pyeval
		let s:has_python = 1
	endif
elseif has('python')
	let s:has_python = 1
	let s:pycmd = 'py'
	let s:pyeval = get(g:, 'powerline_pyeval', 'pyeval')
elseif has('python3')
	let s:has_python = 1
	let s:pycmd = 'py3'
	let s:pyeval = get(g:, 'powerline_pyeval', 'py3eval')
else
	let s:has_python = 0
endif

if !s:has_python
	if !exists('g:powerline_no_python_error')
		echohl ErrorMsg
			echomsg 'You need vim compiled with Python 2.6, 2.7 or 3.2 and later support'
			echomsg 'for Powerline to work. Please consult the documentation for more'
			echomsg 'details.'
		echohl None
	endif
	unlet s:has_python
	finish
endif
unlet s:has_python

let s:import_cmd = 'from powerline.vim import VimPowerline'
function s:rcmd(s)
	if !exists('s:pystr')
		let s:pystr = a:s . "\n"
	else
		let s:pystr = s:pystr . a:s . "\n"
	endif
endfunction
try
	let s:can_replace_pyeval = !exists('g:powerline_pyeval')
	call s:rcmd('try:')
	call s:rcmd('	powerline_appended_path = None')
	call s:rcmd('	try:')
	call s:rcmd('		'.s:import_cmd.'')
	call s:rcmd('	except ImportError:')
	call s:rcmd('		import sys, vim')
	call s:rcmd('		powerline_appended_path = vim.eval("expand(\"<sfile>:h:h:h:h:h\")")')
	call s:rcmd('		sys.path.append(powerline_appended_path)')
	call s:rcmd('		'.s:import_cmd.'')
	call s:rcmd('	import vim')
	call s:rcmd('	powerline_instance = VimPowerline()')
	call s:rcmd('	powerline_instance.setup(pyeval=vim.eval("s:pyeval"), pycmd=vim.eval("s:pycmd"), can_replace_pyeval=int(vim.eval("s:can_replace_pyeval")))')
	call s:rcmd('	del VimPowerline')
	call s:rcmd('	del powerline_instance')
	call s:rcmd('except Exception:')
	call s:rcmd('	import traceback, sys')
	call s:rcmd('	traceback.print_exc(file=sys.stdout)')
	call s:rcmd('	raise')
	execute s:pycmd s:pystr
	unlet s:pystr
	let s:launched = 1
finally
	unlet s:can_replace_pyeval
	unlet s:import_cmd
	if !exists('s:launched')
		unlet s:pystr
		echohl ErrorMsg
			echomsg 'An error occurred while importing powerline module.'
			echomsg 'This could be caused by invalid sys.path setting,'
			echomsg 'or by an incompatible Python version (powerline requires'
			echomsg 'Python 2.6, 2.7 or 3.2 and later to work). Please consult'
			echomsg 'the troubleshooting section in the documentation for'
			echomsg 'possible solutions.'
			if s:pycmd is# 'py' && has('python3')
				echomsg 'If powerline on your system is installed for python 3 only you'
				echomsg 'should set g:powerline_pycmd to "py3" to make it load correctly.'
			endif
		echohl None
		call s:rcmd('def powerline_troubleshoot():')
		call s:rcmd('	import sys')
		call s:rcmd('	import vim')
		call s:rcmd('	if sys.version_info < (2, 6):')
		call s:rcmd('		print("Too old python version: " + sys.version + " (first supported is 2.6)")')
		call s:rcmd('	elif sys.version_info[0] == 3 and sys.version_info[1] < 2:')
		call s:rcmd('		print("Too old python 3 version: " + sys.version + " (first supported is 3.2)")')
		call s:rcmd('	try:')
		call s:rcmd('		import powerline')
		call s:rcmd('	except ImportError:')
		call s:rcmd('		print("Unable to import powerline, is it installed?")')
		call s:rcmd('	else:')
		call s:rcmd('		if not vim.eval(''expand("<sfile>")'').startswith("/usr/"):')
		call s:rcmd('			import os')
		call s:rcmd('			powerline_dir = os.path.realpath(os.path.normpath(powerline.__file__))')
		call s:rcmd('			powerline_dir = os.path.dirname(powerline.__file__)')
		call s:rcmd('			this_dir = os.path.realpath(os.path.normpath(vim.eval(''expand("<sfile>:p")'')))')
		call s:rcmd('			this_dir = os.path.dirname(this_dir)')  " powerline/bindings/vim/plugin
		call s:rcmd('			this_dir = os.path.dirname(this_dir)')  " powerline/bindings/vim
		call s:rcmd('			this_dir = os.path.dirname(this_dir)')  " powerline/bindings
		call s:rcmd('			this_dir = os.path.dirname(this_dir)')  " powerline
		call s:rcmd('			if os.path.basename(this_dir) != "powerline":')
		call s:rcmd('				print("Check your installation:")')
		call s:rcmd('				print("this script is not in powerline[/bindings/vim/plugin] directory,")')
		call s:rcmd('				print("neither it is installed system-wide")')
		call s:rcmd('			real_powerline_dir = os.path.realpath(powerline_dir)')
		call s:rcmd('			real_this_dir = os.path.realpath(this_dir)')
		call s:rcmd('			this_dir_par = os.path.dirname(real_this_dir)')
		call s:rcmd('			powerline_appended_path = globals().get("powerline_appended_path")')
		call s:rcmd('			if powerline_appended_path is not None and this_dir_par != powerline_appended_path:')
		call s:rcmd('				print("Check your installation: this script is symlinked somewhere")')
		call s:rcmd('				print("where powerline is not present: {0!r} != {1!r}.".format(')
		call s:rcmd('					real_this_dir, powerline_appended_path))')
		call s:rcmd('			elif real_powerline_dir != real_this_dir:')
		call s:rcmd('				print("It appears that you have two powerline versions installed:")')
		call s:rcmd('				print("one in " + real_powerline_dir + ", other in " + real_this_dir + ".")')
		call s:rcmd('				print("You should remove one of this. Check out troubleshooting section,")')
		call s:rcmd('				print("it contains some information about the alternatives.")')
		call s:rcmd('		try:')
		call s:rcmd('			from powerline.lint import check')
		call s:rcmd('		except ImportError:')
		call s:rcmd('			print("Failed to import powerline.lint.check, cannot run powerline-lint")')
		call s:rcmd('		else:')
		call s:rcmd('			try:')
		call s:rcmd('				paths = powerline_instance.get_config_paths()')
		call s:rcmd('			except NameError:')
		call s:rcmd('				pass')
		call s:rcmd('			else:')
		call s:rcmd('				from powerline.lint.markedjson.error import echoerr')
		call s:rcmd('				ee = lambda *args, **kwargs: echoerr(*args, stream=sys.stdout, **kwargs)')
		call s:rcmd('				check(paths=paths, echoerr=ee, require_ext="vim")')
		call s:rcmd('try:')
		call s:rcmd('	powerline_troubleshoot()')
		call s:rcmd('finally:')
		call s:rcmd('	del powerline_troubleshoot')
		execute s:pycmd s:pystr
		unlet s:pystr
		unlet s:pycmd
		unlet s:pyeval
		delfunction s:rcmd
		finish
	else
		unlet s:launched
	endif
	unlet s:pycmd
	unlet s:pyeval
	delfunction s:rcmd
endtry
