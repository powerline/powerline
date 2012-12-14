import vim

def help():
    return bool(int(vim.eval('&buftype is# "help"')))

# vim: noet tw=120
