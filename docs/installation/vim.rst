Vim installation
----------------

As a system-wide Python package
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Add the following line to your ``vimrc``::

    python import plugin.vim.load_vim_plugin

Outside Python's search path
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This requires you to source the plugin file with an absolute path to the 
plugin location.

Add the following line to your ``vimrc``, where ``{path}`` is the path to 
the main Powerline project folder::

    source {path}/plugin/vim/powerline.vim
