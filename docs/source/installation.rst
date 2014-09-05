************
Installation
************

Generic requirements
====================

* Python 2.6 or later, 3.2 or later, PyPy 2.0 or later. It is the only 
  non-optional requirement.
* C compiler. Required to build powerline client on linux. If it is not present 
  then powerline will fall back to shell script or python client.
* ``socat`` program. Required for shell variant of client which runs a bit 
  faster than python version of the client, but still slower than C version.
* ``psutil`` python package. Required for some segments like cpu_percent. Some 
  segments have linux-only fallbacks for ``psutil`` functionality.
* ``mercurial`` python package (note: *not* standalone executable). Required to 
  work with mercurial repositories.
* ``pygit2`` python package or ``git`` executable. Required to work with ``git`` 
  repositories.
* ``bzr`` python package (note: *not* standalone executable). Required to work 
  with bazaar repositories.
* ``pyuv`` python package. Required for :ref:`libuv-based watcher 
  <config-common-watcher>` to work.
* ``i3-py``, `available on github <https://github.com/ziberna/i3-py>`_. Required 
  for i3wm bindings and segments.

.. note::
    Until mercurial and bazaar support Python-3 or PyPy powerline will not 
    support repository information when running in these interpreters.

Pip installation
================

This project is currently unavailable from PyPI due to a naming conflict with an 
unrelated project, thus you will have to use the following command to install 
powerline with ``pip``:

.. code-block:: sh

    pip install --user git+git://github.com/Lokaltog/powerline

. You may also choose to clone powerline repository somewhere and use

.. code-block:: sh

    pip install -e --user {path_to_powerline}

, but note that in this case ``pip`` will not install ``powerline`` executable 
and you will have to do something like

.. code-block:: sh

    ln -s {path_to_powerline}/scripts/powerline ~/.local/bin

(:file:`~/.local/bin` should be replaced with some path present in ``$PATH``).

.. note::
    If your ISP blocks git protocol for some reason github also provides ``ssh`` 
    (``git+ssh://git@github.com/Lokaltog/powerline``) and ``https`` 
    (``git+https://github.com/Lokaltog/powerline``) protocols. ``git`` protocol 
    should be the fastest, but least secure one though.

To install release version uploaded to PyPI use

.. code-block:: sh

   pip install powerline-status

Fonts installation
==================

Powerline uses several special glyphs to get the arrow effect and some custom 
symbols for developers. This requires that you either have a symbol font or 
a patched font on your system. Your terminal emulator must also support either 
patched fonts or fontconfig for Powerline to work properly.

You can also enable :ref:`24-bit color support <config-common-term_truecolor>` 
if your terminal emulator supports it (see :ref:`the terminal emulator support 
matrix <usage-terminal-emulators>`).

There are basically two ways to get powerline glyphs displayed: use 
:file:`PowerlineSymbols.otf` font as a fallback for one of the existing fonts or 
install a patched font.

.. _installation-patched-fonts:

Patched fonts
-------------

This method is the fallback method and works for every terminal, with the 
exception of :ref:`rxvt-unicode <tips-and-tricks-urxvt>`.

Download the font of your choice from `powerline-fonts`_. If you can't find 
your preferred font in the `powerline-fonts`_ repo, you'll have to patch your 
own font instead.

.. _powerline-fonts: https://github.com/Lokaltog/powerline-fonts

After downloading this font refer to platform-specific instructions.

Installation on various platforms
=================================

.. toctree::

   Linux <installation/linux>
   OS X <installation/osx>
