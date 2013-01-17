Overview
========

Requirements
------------

Powerline requires Python 2.7 to work.

Vim plugin requirements
^^^^^^^^^^^^^^^^^^^^^^^

The vim plugin requires a vim version with Python 2.7 support compiled in.  
You can check if your vim supports Python 2 by running ``vim --version 
| grep +python``.

If your vim version doesn't have support for Python 2, you'll have to 
compile it with the ``--enable-pythoninterp`` flag (this also requires the 
Python headers to be installed on your system). Please consult your 
distribution's documentation for details on how to compile and install 
packages.

Vim version 7.3.661 or newer is recommended for performance reasons.

Installation
------------

Installing with ``pip``
^^^^^^^^^^^^^^^^^^^^^^^

To install Powerline system-wide, run the following command as root::

    pip install https://github.com/Lokaltog/powerline/tarball/develop

If you don't have root access or don't want to install Powerline 
system-wide, install with ``pip install --user`` instead.

.. note:: Make sure that you install the package for Python 2. For distros 
   like Arch Linux you'll have to run ``pip2`` instead of ``pip``.

.. note:: This project is currently unavailable on the PyPI due to a naming 
   conflict with an unrelated project.

Distribution-specific packages
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The following distribution-specific packages are officially supported, and 
they provide an easy way of installing and upgrading Powerline:

* `Arch Linux (AUR) <https://aur.archlinux.org/packages/powerline-git/>`_

Usage
-----

Vim statusline
^^^^^^^^^^^^^^

If Powerline is installed as a Python package, you can enable the vim plugin 
by adding the following line to your ``vimrc``::

    python from powerline.ext.vim import source_plugin; source_plugin()

If Powerline is installed somewhere other than Python's site-packages 
directories (e.g. by having the git repo in your dotfiles directory) you'll 
have to source the vim plugin file with an absolute path to the plugin 
location.

Add the following line to your ``vimrc``, where ``{path}`` is the path to 
the main Powerline project directory::

    source {path}/powerline/ext/vim/source_plugin.vim

Terminal prompt
^^^^^^^^^^^^^^^

Add the following to your ``.bashrc``/``.zshrc``::

    export PS1=\`powerline-prompt\`

If Powerline is installed somewhere other than Python's site-packages you'll 
have to specify the full path to the script::

    export PS1=\`/path/to/powerline/scripts/powerline-prompt\`

Tmux statusline
^^^^^^^^^^^^^^^

Add the following to your ``tmux.conf``::

    set-option -g status on
    set-option -g status-interval 2
    set-option -g status-utf8 on
    set-option -g status-left-length 100
    set-option -g status-left "#(powerline-tmux left)"
    set-option -g status-right-length 100
    set-option -g status-right "#(powerline-tmux right)"
    set-option -g status-justify "centre"
    set-option -g status-bg "colour235"
    set-option -g status-fg "colour249"

If Powerline is installed somewhere other than Python's site-packages you'll 
have to specify the full path to the script in the ``status-left`` and 
``status-right`` options.
