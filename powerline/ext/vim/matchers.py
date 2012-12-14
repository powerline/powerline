import vim


def help():
	return bool(int(vim.eval('&buftype is# "help"')))
