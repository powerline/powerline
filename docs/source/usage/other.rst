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

(replace ``python`` with ``python3`` if appropriate) to your :file:`vimrc`.

If you just cloned the repository add the following line to your :file:`vimrc`, 
where ``{repository_root}`` is the absolute path to your Powerline installation 
directory:

.. code-block:: vim

   set rtp+={repository_root}/powerline/bindings/vim

If you’re using pathogen and don’t want Powerline functionality in any other 
applications, simply add Powerline as a bundle and point the path above to the 
Powerline bundle directory, e.g. 
``~/.vim/bundle/powerline/powerline/bindings/vim``.

With Vundle you may instead use

.. code-block:: vim

    Bundle 'Lokaltog/powerline', {'rtp': 'powerline/bindings/vim/'}

(replace ``Bundle`` with ``NeoBundle`` for NeoBundle).

For vim-addon-manager it is even easier since you don’t need to write this big 
path or install anything by hand: ``powerline`` is installed and run just like 
any other plugin using

.. code-block:: vim

    call vam#ActivateAddons(['powerline'])

.. warning::
    *Never* install powerline with pathogen/VAM/Vundle/NeoBundle *and* with pip. 
    If you want powerline functionality in vim and other applications use 
    system-wide installation if your system has powerline package, pip-only or 
    ``pip install --editable`` kind of installation performed on the repository 
    installed by Vim plugin manager.

    If you have installed powerline with pip and with some of Vim package 
    managers do never report any errors to powerline bug tracker, especially 
    errors occurring after updates.

.. note::
    If you use supplied :file:`powerline.vim` file to load powerline there are 
    additional configuration variables available: ``g:powerline_pycmd`` and 
    ``g:powerline_pyeval``. First sets command used to load powerline: expected 
    values are ``"py"`` and ``"py3"``. Second sets function used in statusline, 
    expected values are ``"pyeval"`` and ``"py3eval"``.

    If ``g:powerline_pycmd`` is set to the one of the expected values then 
    ``g:powerline_pyeval`` will be set accordingly. If it is set to some other 
    value then you must also set ``g:powerline_pyeval``. Powerline will not 
    check that Vim is compiled with Python support if you set 
    ``g:powerline_pycmd`` to an unexpected value.

    These values are to be used to specify the only Python that is to be loaded 
    if you have both versions: Vim may disable loading one python version if 
    other was already loaded. They should also be used if you have two python 
    versions able to load simultaneously, but with powerline installed only for 
    python-3 version.

Tmux statusline
===============

Add the following lines to your :file:`.tmux.conf`, where ``{repository_root}`` 
is the absolute path to your Powerline installation directory::

   source "{repository_root}/powerline/bindings/tmux/powerline.conf"

.. note::
    The availability of the ``powerline-config`` command is required for 
    powerline support. You may specify location of this script via 
    ``$POWERLINE_CONFIG_COMMAND`` environment variable.

.. note::
    It is advised that you run ``powerline-daemon`` before adding the above line 
    to tmux.conf. To do so add::

        run-shell "powerline-daemon -q"

    to :file:`.tmux.conf`.

IPython prompt
==============

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
