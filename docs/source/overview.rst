********
Overview
********

Requirements
============

Powerline requires Python 3.3 or Python 2.7 to work.

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

Terminal emulator requirements
------------------------------

Powerline uses several special glyphs to get the arrow effect and some 
custom symbols for developers. This requires that you either have a symbol 
font or a patched font on your system. Your terminal emulator must also 
support either patched fonts or fontconfig for Powerline to work properly.

You can also enable :ref:`24-bit color support <config-term_24bit_colors>` 
if your terminal emulator supports it.

.. table:: Application/terminal emulator feature support matrix
   :name: term-feature-support-matrix

   ===================== ======= ===================== ===================== =====================
   Name                  OS      Patched font support  Fontconfig support    24-bit color support 
   ===================== ======= ===================== ===================== =====================
   Gnome Terminal        Linux   |i_yes|               |i_yes|               |i_no|
   Gvim                  Linux   |i_yes|               |i_no|                |i_yes|
   iTerm2                OS X    |i_yes|               |i_no|                |i_no|
   Konsole               Linux   |i_yes|               |i_yes|               |i_yes|
   lxterminal            Linux   |i_yes|               |i_yes|               |i_no|
   MacVim                OS X    |i_yes|               |i_no|                |i_yes|
   rxvt-unicode          Linux   |i_partial| [#]_      |i_no|                |i_no|
   st                    Linux   |i_yes|               |i_yes|               |i_no|
   Terminal.app          OS X    |i_yes|               |i_no|                |i_no|
   Xfce Terminal         Linux   |i_yes|               |i_yes|               |i_no|
   xterm                 Linux   |i_yes|               |i_no|                |i_partial| [#]_
   ===================== ======= ===================== ===================== =====================

.. |i_yes| image:: _static/img/icons/tick.png
.. |i_no| image:: _static/img/icons/cross.png
.. |i_partial| image:: _static/img/icons/error.png

.. [#] Must be compiled with ``--enable-unicode3`` for the 
   patched font to work.
.. [#] Uses nearest color from 8-bit palette.

Optional dependencies
---------------------

The following Python packages are not required by all segments, but 
recommended for optimal performance and extra features:

* ``pygit2``
* ``mercurial``
* ``psutil``

Installation
============

* :ref:`installation-linux`
* :ref:`installation-osx`

Usage
=====

Vim statusline
--------------

Add the following line to your :file:`vimrc`:

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

For ipython<0.11 add the following lines to your 
:file:`.ipython/ipy_user_conf.py`::

  # top
  from powerline.bindings.ipython import setup as powerline_setup

  # main() function (assuming you launched ipython without configuration to 
  # create skeleton ipy_user_conf.py file):
  powerline_setup()

For ipython>=0.11 add the following line to your ipython_config.py file in the 
profile you are using::

  c.InteractiveShellApp.extensions = [
    'powerline.bindings.ipython'
  ]
