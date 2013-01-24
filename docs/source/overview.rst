********
Overview
********

Requirements
============

Powerline requires Python 3.3 or Python 2.7 to work.

Powerline uses several special glyphs to get the arrow effect and some 
custom symbols for developers. This requires that you either have the symbol 
font or a patched font on your system. See `Font installation`_ for more 
details.

Vim plugin requirements
-----------------------

The vim plugin requires a vim version with Python support compiled in.  You 
can check if your vim supports Python by running ``vim --version | grep 
+python``.

If your vim version doesn't have support for Python, you'll have to compile 
it with the ``--enable-pythoninterp`` flag (``--enable-python3interp`` if 
you want Python 3 support instead). Note that this also requires the related 
Python headers to be installed on your system. Please consult your 
distribution's documentation for details on how to compile and install 
packages.

Vim version 7.3.661 or newer is recommended for performance reasons.

Optional dependencies
---------------------

The following Python packages are not required by all segments, but 
recommended for optimal performance and extra features:

* ``pygit2``
* ``mercurial``
* ``psutil``

Installation
============

Installing with ``pip``
-----------------------

To install Powerline system-wide, run the following command as root::

    pip install git+git://github.com/Lokaltog/powerline

If you don't have root access or don't want to install Powerline 
system-wide, install with ``pip install --user`` instead.

.. note:: This project is currently unavailable on the PyPI due to a naming 
   conflict with an unrelated project.

Distribution-specific packages
------------------------------

The following distribution-specific packages are officially supported, and 
they provide an easy way of installing and upgrading Powerline:

* `Arch Linux (AUR) <https://aur.archlinux.org/packages/powerline-git/>`_
* Gentoo Live ebuild (:file:`packages/gentoo/app-misc/powerline/`)

.. _font-installation:

Font installation
-----------------

Linux
^^^^^

If you're running Linux, you may be able to avoid patching your coding font 
to get the special glyphs required by Powerline. This works by utilizing 
fontconfig's fallback font feature, which replaces missing glyphs in a font 
with another font on your system.

This has been tested and works very well with many different coding fonts, 
but some fonts may look terrible, in which case you'll have to use a patched 
font (see :ref:`font-patching` for details).

1. Download the `latest version of PowerlineSymbols 
   <https://github.com/Lokaltog/powerline/raw/develop/font/PowerlineSymbols.otf>`_  
   and the `latest version of the fontconfig file 
   <https://github.com/Lokaltog/powerline/raw/develop/font/10-powerline-symbols.conf>`_.
2. Move :file:`PowerlineSymbols.otf` to :file:`~/.fonts/`.
3. Run ``fc-cache -vf ~/.fonts`` to update your font cache.
4. Move :file:`10-powerline-symbols.conf` to either :file:`~/.fonts.conf.d/` 
   or :file:`~/.config/fontconfig/conf.d/`, depending on your fontconfig 
   version.
5. If you don't see the arrow symbols, please close all instances of your 
   terminal emulator or gvim. You may also have to restart X for the changes 
   to take effect. If you *still* don't see the arrow symbols, please submit 
   an issue on GitHub.

OS X and Windows
^^^^^^^^^^^^^^^^

You'll have to use a patched font to use the Powerline symbols. See 
:ref:`font-patching` for details on font patching and pre-patched fonts.

Usage
=====

.. note:: If Powerline is installed somewhere other than Python's 
   site-packages directories (e.g. by having the git repo in your dotfiles 
   directory) you'll have to use the absolute path to the scripts in the 
   examples below.

Vim statusline
--------------

Regular installation
^^^^^^^^^^^^^^^^^^^^

**The recommended way of installing Powerline is as a Python package.**
You can then enable the vim plugin by adding the following line to your 
:file:`vimrc`:

.. code-block:: vim

   python from powerline.bindings.vim import source_plugin; source_plugin()

If you want to enable Python 3 support, substitute the ``python`` command 
above with ``python3``. Note that this is somewhat experimental as some 
segments don't have support for Python 3 yet.

If Powerline is installed somewhere other than Python's site-packages 
directories you'll either have to use a plugin manager like Vundle, or 
source the vim plugin file with an absolute path to the plugin location.

Add the following line to your :file:`vimrc`, where ``{path}`` is the path 
to the main Powerline project directory:

.. code-block:: vim

   source {path}/powerline/bindings/vim/plugin/source_plugin.vim

Vundle installation
^^^^^^^^^^^^^^^^^^^

If you're using Vundle you can add the following line to your :file:`vimrc`:

.. code-block:: vim

   Bundle 'Lokaltog/powerline', {'rtp': 'powerline/bindings/vim/'}

Shell prompts
-------------

Bash prompt
^^^^^^^^^^^

Add the following line to your :file:`bashrc`, where ``{path}`` is the 
absolute path to your Powerline installation directory:

.. code-block:: bash

   . {path}/powerline/bindings/bash/powerline.sh

Zsh prompt
^^^^^^^^^^

Add the following line to your :file:`zshrc`, where ``{path}`` is the 
absolute path to your Powerline installation directory:

.. code-block:: bash

   . {path}/powerline/bindings/zsh/powerline.zsh

Tmux statusline
^^^^^^^^^^^^^^^

Add the following line to your :file:`tmux.conf`, where ``{path}`` is the 
absolute path to your Powerline installation directory::

   source '{path}/powerline/bindings/tmux/powerline.conf'

Ipython prompt
^^^^^^^^^^^^^^

Add the following lines to your :file:`.ipython/ipy_user_conf.py`::

  # top
  from powerline.bindings.ipython import setup as powerline_setup

  # main() function (assuming you launched ipython without configuration to 
  # create skeleton ipy_user_conf.py file):
  powerline_setup()

The following theoretically works, if you can figure out where to put it (I saw 
a big bunch of wiki pages suggesting to put it somewhere, but have no idea where 
actually)::

  c.InteractiveShellApp.extensions = [
    'powerline.bindings.ipython'
  ]
