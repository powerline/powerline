python import cProfile
python powerline_pr = cProfile.Profile()

function powerline#debug#profile_pyeval(s)
	python powerline_pr.enable()
	try
		let ret = pyeval(a:s)
	finally
		python powerline_pr.disable()
	endtry
	return ret
endfunction

function powerline#debug#write_profile(fname)
	python import vim
	python powerline_pr.dump_stats(vim.eval('a:fname'))
	python powerline_pr = cProfile.Profile()
endfunction

command -nargs=1 -complete=file WriteProfiling :call powerline#debug#write_profile(<q-args>)
