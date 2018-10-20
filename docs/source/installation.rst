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


Pip installation
================

Refer to :ref:`install-osx` or :ref:`install-linux` for platform-specific
instructions. If these do not apply to you, apply the following steps.

- To install the latest release, run:

  .. code-block:: sh

     pip install powerline-status

  .. note:: Due to a naming conflict with an unrelated project, Powerline
     is available on PyPi under the ``powerline-status`` name.

- To install the current development version, run:

  .. code-block:: sh

     pip install --user git+git://github.com/powerline/powerline

- If powerline was already checked out into some directory

  .. code-block:: sh

     pip install --user --editable={path_to_powerline}

  .. note:: In this case ``pip`` will not install ``powerline``
     executable. You might need to run:

     .. code-block:: sh

        ln -s {path_to_powerline}/scripts/powerline ~/.local/bin

     (:file:`~/.local/bin` should be replaced with some path
     present in ``$PATH``).

.. note::
   If your ISP blocks the git protocol for some reason, use the following
   Github protocols:

   - ``ssh``: ``git+ssh://git@github.com/powerline/powerline``
   - ``https``: ``git+https://github.com/powerline/powerline``

   The ``git`` protocol should be the fastest, but the least secure one.

.. _repository-root:

.. rubric:: Repository root

Since you used ``pip`` to install powerline, you will need to know the
``{repository_root}`` directory to set up powerline.

To display the ``{repository_root}``:

#. Run ``pip show powerline-status``.
#. Find the output line containing ``Location: {path}``. That ``{path}``
   is the ``{repository_root}``.

Unless you used the ``--editable`` flag during the installation, this is
only applicable for ``{repository_root}/powerline/…`` paths: something
like ``{repository_root}/scripts/powerline-render`` is not present.

When using other packages referenced paths may not exist, in this case refer
to the package documentation.

Fonts installation
==================

Powerline uses several special glyphs to get the arrow effect and some custom
symbols for developers. This requires having either a symbol font or a patched
font installed in the system.

The used application (e.g. terminal emulator) must
also either be configured to use patched fonts (in some cases even support it
because custom glyphs live in private use area which some applications reserve
for themselves) or support fontconfig for powerline to work properly with
powerline-specific glyphs.

:ref:`24-bit color support <config-common-term_truecolor>` may be enabled if
used terminal emulator supports it (see :ref:`the terminal emulator support
matrix <usage-terminal-emulators>`).

There are 2 ways to get powerline glyphs displayed:

#. Use :file:`PowerlineSymbols.otf` font as a fallback for one of the existing
   fonts, or
#. :ref:`Install a patched font <installation-patched-fonts>`.

.. _installation-patched-fonts:

Installing patched fonts
------------------------

This method is the fallback method and works for every terminal.

#. Download the font from `powerline-fonts`_.
#. Find the font you wish to use and install it following the repo's readme.

   If the preferred fonts can’t be found in the `powerline-fonts`_ repo,
   then patching the preferred font is needed.

.. _powerline-fonts: https://github.com/powerline/fonts


Installation on various platforms
=================================

.. toctree::

   Linux <installation/linux>
   OS X <installation/osx>
