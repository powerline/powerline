*************
Other plugins
*************

.. _vim-vimrc:

Vim statusline
==============

If installed using pip just add

.. code-block:: vim

    python from powerline.vim import setup as powerline_setup
    python powerline_setup()
    python del powerline_setup

(replace ``python`` with ``python3`` if appropriate) to the :file:`vimrc`.

If the repository was just cloned the following line needs to be added to the 
:file:`vimrc`:

.. code-block:: vim

   set rtp+={repository_root}/powerline/bindings/vim

where ``{repository_root}`` is the absolute path to the Powerline installation 
directory.

If pathogen is used and Powerline functionality is not needed outside of Vim 
then it is possible to simply add Powerline as a bundle and point the path above 
to the Powerline bundle directory, e.g. 
:file:`~/.vim/bundle/powerline/powerline/bindings/vim`.

Vundle and NeoBundle users may instead use

.. code-block:: vim

    Bundle 'powerline/powerline', {'rtp': 'powerline/bindings/vim/'}

(NeoBundle users need ``NeoBundle`` in place of ``Bundle``, otherwise setup is 
the same).

Vim-addon-manager setup is even easier because it is not needed to write this 
big path or install anything by hand: ``powerline`` can be installed and 
activated just like any other plugin using

.. code-block:: vim

    call vam#ActivateAddons(['powerline'])

.. warning::
    *Never* install powerline with pathogen/VAM/Vundle/NeoBundle *and* with pip. 
    If powerline functionality is needed in applications other then Vim then 
    system-wide installation (in case used OS distribution has powerline 
    package), pip-only or ``pip install --editable`` kind of installation 
    performed on the repository installed by Vim plugin manager should be used.

    No issues are accepted in powerline issue tracker for double pip/non-pip 
    installations, especially if these issues occur after update.

.. note::
    If supplied :file:`powerline.vim` file is used to load powerline there are 
    additional configuration variables available: ``g:powerline_pycmd`` and 
    ``g:powerline_pyeval``. First sets command used to load powerline: expected 
    values are ``"py"`` and ``"py3"``. Second sets function used in statusline, 
    expected values are ``"pyeval"`` and ``"py3eval"``.

    If ``g:powerline_pycmd`` is set to the one of the expected values then 
    ``g:powerline_pyeval`` will be set accordingly. If it is set to some other 
    value then ``g:powerline_pyeval`` must also be set. Powerline will not check 
    that Vim is compiled with Python support if ``g:powerline_pycmd`` is set to 
    an unexpected value.

    These values are to be used to specify the only Python that is to be loaded 
    if both versions are present: Vim may disable loading one python version if 
    other was already loaded. They should also be used if two python versions 
    are able to load simultaneously, but powerline was installed only for 
    python-3 version.

Tmux statusline
===============

Add the following lines to :file:`.tmux.conf`, where ``{repository_root}`` is 
the absolute path to the Powerline installation directory::

   source "{repository_root}/powerline/bindings/tmux/powerline.conf"

.. note::
    The availability of the ``powerline-config`` command is required for 
    powerline support. DLlocation of this script may be specified via 
    ``$POWERLINE_CONFIG_COMMAND`` environment variable.

.. note::
    It is advised to run ``powerline-daemon`` before adding the above line to 
    tmux.conf. To do so add::

        run-shell "powerline-daemon -q"

    to :file:`.tmux.conf`.

IPython prompt
==============

For IPython<0.11 add the following lines to :file:`.ipython/ipy_user_conf.py`:

.. code-block:: Python

    # top
    from powerline.bindings.ipython.pre_0_11 import setup as powerline_setup

    # main() function (assuming ipython was launched without configuration to 
    # create skeleton ipy_user_conf.py file):
    powerline_setup()

For IPython>=0.11 add the following line to :file:`ipython_config.py` file in 
the used profile:

.. code-block:: Python

    c.InteractiveShellApp.extensions = [
        'powerline.bindings.ipython.post_0_11'
    ]

IPython=0.11* is not supported and does not work. IPython<0.10 was not 
tested (not installable by pip).

.. _pdb-prompt:

PDB prompt
==========

To use Powerline with PDB prompt you need to use custom class. Inherit your 
class from :py:class:`pdb.Pdb` and decorate it with 
:py:func:`powerline.bindings.pdb.use_powerline_prompt`:

.. code-block:: Python

   import pdb

   from powerline.bindings.pdb import use_powerline_prompt

   @use_powerline_prompt
   class MyPdb(pdb.Pdb):
       pass

   MyPdb.run('some.code.to.debug()')

. Alternatively you may use

.. code-block:: bash

   python -mpowerline.bindings.pdb path/to/script.py

just like you used ``python -m pdb``.

.. note:
   If you are using Python-2.6 you need to use ``python 
   -mpowerline.bindings.pdb.__main__``, not what is shown above.

.. warning:
   Using PyPy (not PyPy3) forces ASCII-only prompts. In other cases unicode 
   characters are allowed, even if you use `pdbpp 
   <https://pypi.python.org/pypi/pdbpp>`_.
