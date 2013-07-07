if exists('g:powerline_loaded')
    finish
endif
let g:powerline_loaded = 1

if ! has('python') && ! has('python3')
	if !exists('g:powerline_no_python_error')
		echohl ErrorMsg
			echom 'You need vim compiled with Python 2.6, 2.7 or 3.2 and later support'
			echom 'for Powerline to work. Please consult the documentation for more'
			echom 'details.'
		echohl None
	endif
	finish
endif

let s:pycmd = substitute(get(g:, 'powerline_pycmd', has('python') ? 'py' : 'py3'), '\v^(py)%[thon](3?)$', '\1\2', '')
let s:pyeval = get(g:, 'powerline_pyeval', s:pycmd.'eval')

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
	if !exists('s:launched')
		echohl ErrorMsg
			echom 'An error occurred while importing powerline package.'
			echom 'This could be caused by invalid sys.path setting,'
			echom 'or by an incompatible Python version (powerline requires'
			echom 'Python 2.6, 2.7 or 3.2 and later to work). Please consult'
			echom 'the troubleshooting section in the documentation for'
			echom 'possible solutions.'
		echohl None
		finish
	else
		unlet s:launched
	endif
endtry

execute s:pycmd 'import vim'
execute s:pycmd 'powerline_setup(pyeval=vim.eval("s:pyeval"), pycmd=vim.eval("s:pycmd"))'
execute s:pycmd 'del powerline_setup'
