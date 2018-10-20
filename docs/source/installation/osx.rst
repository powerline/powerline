.. _install-osx:

********************
Installation on OS X
********************

Installing Python
=================

#. Install a proper Python version (see `issue #39
   <https://github.com/powerline/powerline/issues/39>`_ for a discussion
   regarding the required Python version on OS X).

   Use either::

       sudo port select python python27-apple

   Or Homebrew::

       brew install python

   .. note::
      In case you use :file:`powerline.sh` as a client, install ``socat`` and
      ``coreutils``. ``coreutils`` may be installed using ``brew install
      coreutils``.

#. Install Powerline using one of the following commands:

   .. warning::
      When using ``brew install`` to install Python one must not supply
      ``--user`` flag to ``pip``.

   .. note::
      Due to the naming conflict with an unrelated project, powerline is named
      ``powerline-status`` in PyPI.

   - Latest version:

     .. code-block:: sh

        pip install --user powerline-status

   - Development version:

     .. code-block:: sh

        pip install --user git+git://github.com/powerline/powerline


   .. note::
      Powerline developers should be aware that ``pip install --editable`` does
      not currently fully work. Installation performed this way are missing
      ``powerline`` executable that needs to be symlinked. It will be located in
      ``scripts/powerline``.

Installing vim
==============

Any terminal vim version with Python 3.2+ or Python 2.6+ support should work.

If you use MacVim, install it using the following command:

.. code-block:: sh

   brew install macvim --env-std --with-override-system-vim

Installing fonts
================

To install a patched font:

#. Download the font from the `powerline-fonts`_ repository.
#. Double-click the patched font file in Finder. Patched fonts end with
   *for Powerline*.
#. Click :guilabel:`Install this font` in the preview window.
#. Configure your terminal/MacVim/whatever application powerline should work
   with to use the patched font.

Powerline is still not enabled. Refer to :ref:`usage` to enable it.

.. _powerline-fonts: https://github.com/powerline/fonts
