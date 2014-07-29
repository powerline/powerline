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
	finish
endif
unlet s:has_python

let s:import_cmd = 'from powerline.vim import setup as powerline_setup'
try
	let s:pystr  = "try:\n"
	let s:pystr .= "	".s:import_cmd."\n"
	let s:pystr .= "except ImportError:\n"
	let s:pystr .= "	import sys, vim\n"
	let s:pystr .= "	sys.path.append(vim.eval('expand(\"<sfile>:h:h:h:h:h\")'))\n"
	let s:pystr .= "	".s:import_cmd."\n"
	execute s:pycmd s:pystr
	unlet s:pystr
	let s:launched = 1
finally
	unlet s:import_cmd
	if !exists('s:launched')
		echohl ErrorMsg
			echomsg 'An error occurred while importing powerline package.'
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
		let s:pystr  =     "def powerline_troubleshoot():\n"
		let s:pystr .=     "	import sys\n"
		let s:pystr .=     "	if sys.version_info < (2, 6):\n"
		let s:pystr .=     "		print('Too old python version: ' + sys.version + ' (first supported is 2.6)')\n"
		let s:pystr .=     "	elif sys.version_info[0] == 3 and sys.version_info[1] < 2:\n"
		let s:pystr .=     "		print('Too old python 3 version: ' + sys.version + ' (first supported is 3.2)')\n"
		let s:pystr .=     "	try:\n"
		let s:pystr .=     "		import powerline\n"
		let s:pystr .=     "	except ImportError:\n"
		let s:pystr .=     "		print('Unable to import powerline, is it installed?')\n"
		if expand('<sfile>')[:4] isnot# '/usr/'
			let s:pystr .= "	else:\n"
			let s:pystr .= "		import os\n"
			let s:pystr .= "		powerline_dir = os.path.dirname(os.path.realpath(powerline.__file__))\n"
			let s:pystr .= "		this_dir = os.path.dirname(os.path.realpath(vim.eval('expand(\"<sfile>:p\")')))\n"
			let s:pystr .= "		this_dir = os.path.dirname(os.path.dirname(os.path.dirname(this_dir)))\n"
			let s:pystr .= "		if os.path.basename(this_dir) != 'powerline':\n"
			let s:pystr .= "			print('Check your installation:')\n"
			let s:pystr .= "			print('this script is not in powerline[/bindings/vim/plugin] directory,')\n"
			let s:pystr .= "			print('neither it is installed system-wide')\n"
			let s:pystr .= "		this_dir = os.path.dirname(this_dir)\n"
			let s:pystr .= "		real_powerline_dir = os.path.realpath(powerline_dir)\n"
			let s:pystr .= "		real_this_dir = os.path.realpath(this_dir)\n"
			let s:pystr .= "		if real_this_dir != sys.path[-1]:\n"
			let s:pystr .= "			print('Check your installation:')\n"
			let s:pystr .= "			print('this script is symlinked somewhere where powerline is not present.')\n"
			let s:pystr .= "		elif real_powerline_dir != real_this_dir:\n"
			let s:pystr .= "			print('It appears that you have two powerline versions installed:')\n"
			let s:pystr .= "			print('one in ' + real_powerline_dir + ', other in ' + real_this_dir + '.')\n"
			let s:pystr .= "			print('You should remove one of this. Check out troubleshooting section,')\n"
			let s:pystr .= "			print('it contains some information about the alternatives.')\n"
		endif
		execute s:pycmd s:pystr
		unlet s:pystr
		unlet s:pycmd
		unlet s:pyeval
		finish
	else
		unlet s:launched
	endif
endtry

let s:can_replace_pyeval = !exists('g:powerline_pyeval')

execute s:pycmd 'import vim'
execute s:pycmd 'powerline_setup(pyeval=vim.eval("s:pyeval"), pycmd=vim.eval("s:pycmd"), can_replace_pyeval=int(vim.eval("s:can_replace_pyeval")))'
execute s:pycmd 'del powerline_setup'

unlet s:can_replace_pyeval
unlet s:pycmd
unlet s:pyeval
