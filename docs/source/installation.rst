************
Installation
************

Generic requirements
====================

* Python 2.6 or later, 3.2 or later, PyPy 2.0 or later, PyPy3 2.3 or later. It 
  is the only non-optional requirement.

  .. warning:
     It is highly advised to use UCS-4 version of Python because UCS-2 version 
     uses significantly slower text processing (length determination and 
     non-printable character replacement) functions due to the need of 
     supporting unicode characters above U+FFFF which are represented as 
     surrogate pairs. This price will be paid even if configuration has no such 
     characters.

* C compiler. Required to build powerline client on linux. If it is not present 
  then powerline will fall back to shell script or python client.
* ``socat`` program. Required for shell variant of client which runs a bit 
  faster than python version of the client, but still slower than C version.
* ``psutil`` python package. Required for some segments like cpu_percent. Some 
  segments have linux-only fallbacks for ``psutil`` functionality.
* ``hglib`` python package *and* mercurial executable. Required to work with
  mercurial repositories.
* ``pygit2`` python package or ``git`` executable. Required to work with ``git`` 
  repositories.
* ``bzr`` python package (note: *not* standalone executable). Required to work 
  with bazaar repositories.
* ``pyuv`` python package. Required for :ref:`libuv-based watcher 
  <config-common-watcher>` to work.
* ``i3ipc`` python package. Required for i3wm bindings and segments.
* ``xrandr`` program. Required for the multi-monitor lemonbar binding and the 
  :py:func:`powerline.listers.i3wm.output_lister`.

.. note::
    Until bazaar supports Python-3 or PyPy powerline will not support
    repository information when running in these interpreters.

.. _repository-root:

.. note::
   When using ``pip``, the ``{repository_root}`` directory referenced in 
   documentation may be found using ``pip show powerline-status``. In the output 
   of ``pip show`` there is a line like ``Location: {path}``, that ``{path}`` is 
   ``{repository_root}``. Unless it is ``--editable`` installation this is only 
   applicable for ``{repository_root}/powerline/…`` paths: something like 
   ``{repository_root}/scripts/powerline-render`` is not present.

   When using other packages referenced paths may not exist, in this case refer 
   to package documentation.

Pip installation
================

Due to a naming conflict with an unrelated project powerline is available on 
PyPI under the ``powerline-status`` name:

.. code-block:: sh

    pip install powerline-status

is the preferred method because this will get the latest release. To get current 
development version

.. code-block:: sh

    pip install --user git+git://github.com/powerline/powerline

may be used. If powerline was already checked out into some directory

.. code-block:: sh

    pip install --user --editable={path_to_powerline}

is useful, but note that in this case ``pip`` will not install ``powerline`` 
executable and something like

.. code-block:: sh

    ln -s {path_to_powerline}/scripts/powerline ~/.local/bin

will have to be done (:file:`~/.local/bin` should be replaced with some path 
present in ``$PATH``).

.. note::
    If ISP blocks git protocol for some reason github also provides ``ssh`` 
    (``git+ssh://git@github.com/powerline/powerline``) and ``https`` 
    (``git+https://github.com/powerline/powerline``) protocols. ``git`` protocol 
    should be the fastest, but least secure one though.

Fonts installation
==================

Powerline uses several special glyphs to get the arrow effect and some custom 
symbols for developers. This requires having either a symbol font or a patched 
font installed in the system. The used application (e.g. terminal emulator) must 
also either be configured to use patched fonts (in some cases even support it 
because custom glyphs live in private use area which some applications reserve 
for themselves) or support fontconfig for powerline to work properly with 
powerline-specific glyphs.

:ref:`24-bit color support <config-common-term_truecolor>` may be enabled if 
used terminal emulator supports it (see :ref:`the terminal emulator support 
matrix <usage-terminal-emulators>`).

There are basically two ways to get powerline glyphs displayed: use 
:file:`PowerlineSymbols.otf` font as a fallback for one of the existing fonts or 
install a patched font.

.. _installation-patched-fonts:

Patched fonts
-------------

This method is the fallback method and works for every terminal.

Download the font from `powerline-fonts`_. If preferred font can’t be found in 
the `powerline-fonts`_ repo, then patching the preferred font is needed instead.

.. _powerline-fonts: https://github.com/powerline/fonts

After downloading this font refer to platform-specific instructions.

Installation on various platforms
=================================

.. toctree::

   Linux <installation/linux>
   OS X <installation/osx>
