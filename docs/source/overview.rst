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

You can also enable :ref:`24-bit color support <config-common-term_truecolor>` 
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

The following software is not required by all segments, but recommended for 
optimal performance and extra features:

Python packages
^^^^^^^^^^^^^^^

* ``pygit2``
* ``mercurial``
* ``psutil``
* ``i3-py``, `available on github <https://github.com/ziberna/i3-py>`_. Only used with i3wm bindings and segments.

Other applications
^^^^^^^^^^^^^^^^^^

* ``git`` version 1.7.2 and later. Not needed if you have ``pygit2``.

Installation
============

.. note:: This project is currently unavailable from PyPI due to a naming conflict 
   with an unrelated project. Please read the detailed instructions for your platform
   below.

* :ref:`installation-linux`
* :ref:`installation-osx`

Usage
=====

.. _vim-vimrc:

Vim statusline
--------------

If installed using pip just add

.. code-block:: vim

    python from powerline.vim import setup as powerline_setup
    python powerline_setup()
    python del powerline_setup

(replace ``python`` with ``python3`` if appropriate) to your :file:`vimrc`.

If you just cloned the repository add the following line to your :file:`vimrc`, 
where ``{repository_root}`` is the absolute path to your Powerline installation 
directory:

.. code-block:: vim

   set rtp+={repository_root}/powerline/bindings/vim

If you're using Vundle or Pathogen and don't want Powerline functionality in 
any other applications, simply add Powerline as a bundle and point the path 
above to the Powerline bundle directory, e.g. 
``~/.vim/bundle/powerline/powerline/bindings/vim``. For vim-addon-manager it is 
even easier since you don’t need to write this big path or install anything by 
hand: ``powerline`` is installed and run just like any other plugin using

.. code-block:: vim

    call vam#ActivateAddons(['powerline'])

Note: when using Gentoo ebuild you need to specify ``USE=vim`` to enable 
powerline.

Shell prompts
-------------

Bash prompt
^^^^^^^^^^^

Add the following line to your :file:`bashrc`, where ``{repository_root}`` is 
the absolute path to your Powerline installation directory:

.. code-block:: bash

   . {repository_root}/powerline/bindings/bash/powerline.sh

Zsh prompt
^^^^^^^^^^

Add the following line to your :file:`zshrc`, where ``{repository_root}`` is the 
absolute path to your Powerline installation directory:

.. code-block:: bash

   . {repository_root}/powerline/bindings/zsh/powerline.zsh

Fish prompt
^^^^^^^^^^^

Add the following line to your :file:`config.fish`, where ``{repository_root}`` 
is the absolute path to your Powerline installation directory:

.. code-block:: bash

   set fish_function_path $fish_function_path "{repository_root}/powerline/bindings/fish"
   powerline-setup

Tmux statusline
---------------

Add the following line to your :file:`tmux.conf`, where ``{repository_root}`` is 
the absolute path to your Powerline installation directory::

   source '{repository_root}/powerline/bindings/tmux/powerline.conf'

IPython prompt
--------------

For IPython<0.11 add the following lines to your 
:file:`.ipython/ipy_user_conf.py`::

    # top
    from powerline.bindings.ipython.pre_0_11 import setup as powerline_setup

    # main() function (assuming you launched ipython without configuration to 
    # create skeleton ipy_user_conf.py file):
    powerline_setup()

For IPython>=0.11 add the following line to your :file:`ipython_config.py` 
file in the profile you are using::

    c.InteractiveShellApp.extensions = [
        'powerline.bindings.ipython.post_0_11'
    ]

IPython=0.11* is not supported and does not work. IPython<0.10 was not 
tested (not installable by pip).

Awesome widget
--------------

.. note:: Powerline currently only supports awesome 3.5.

.. note:: The Powerline widget will spawn a shell script that runs in the 
   background and updates the statusline with ``awesome-client``.

Add the following to your :file:`rc.lua`, where ``{repository_root}`` is the 
absolute path to your Powerline installation directory:

.. code-block:: lua

   package.path = package.path .. ';{repository_root}/powerline/bindings/awesome/?.lua'
   require('powerline')

Then add the ``powerline_widget`` to your ``wibox``:

.. code-block:: lua

   right_layout:add(powerline_widget)

Qtile widget
------------

Add the following to your :file:`~/.config/qtile/config.py`:

.. code-block:: python

   from powerline.bindings.qtile.widget import Powerline

   screens = [
       Screen(
           top=bar.Bar([
                   # ...
                   Powerline(timeout=2),
                   # ...
               ],
           ),
       ),
   ]

I3 bar
------

.. note:: Until the patch is done in i3, you will need a custom ``i3bar`` build
          called ``i3bgbar``. The source is available `here 
          <https://github.com/S0lll0s/i3bgbar>`_.

Add the following to your :file:`~/.i3/config`::

    bar {
        i3bar_command i3bgbar

        status_command python /path/to/powerline/bindings/i3/powerline-i3.py
        font pango:PowerlineFont 12
    }

where ``i3bgbar`` may be replaced with the path to the custom i3bar binary and 
``PowerlineFont`` is any system font with powerline support.
