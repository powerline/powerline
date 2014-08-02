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
* ``i3-py``, `available on github <https://github.com/ziberna/i3-py>`_. Required 
  for i3wm bindings and segments.

.. note::
    Until mercurial and bazaar support Python-3 or PyPy powerline will not 
    support repository information when running in these interpreters.

Pip installation
================

This project is currently unavailable from PyPI due to a naming conflict with an 
unrelated project, thus you will have to use the following command to install 
powerline with ``pip``::

    pip install --user git+git://github.com/Lokaltog/powerline

. You may also choose to clone powerline repository somewhere and use::

    pip install -e --user {path_to_powerline}

, but note that in this case ``pip`` will not install ``powerline`` executable 
and you will have to do something like::

    ln -s {path_to_powerline}/scripts/powerline ~/.local/bin

(:file:`~/.local/bin` should be replaced with some path present in ``$PATH``).

Installation on various platforms
=================================

.. toctree::

   Linux <installation/linux>
   OS X <installation/osx>
