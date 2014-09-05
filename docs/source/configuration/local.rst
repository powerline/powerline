.. _local-configuration-overrides:

*****************************
Local configuration overrides
*****************************

Depending on the application used it is possible to override configuration. Here 
is the list:

Vim overrides
=============

Vim configuration can be overridden using the following options:

``g:powerline_config_overrides``
    Dictionary, recursively merged with contents of 
    :file:`powerline/config.json`.

``g:powerline_theme_overrides__{theme_name}``
    Dictionary, recursively merged with contents of 
    :file:`powerline/themes/vim/{theme_name}.json`. Note that this way you can’t 
    redefine some value (e.g. segment) in list, only the whole list itself: only 
    dictionaries are merged recursively.

``g:powerline_config_paths``
    Paths list (each path must be expanded, ``~`` shortcut is not supported). 
    Points to the list of directories which will be searched for configuration. 
    When this option is present, none of the other locations are searched.

``g:powerline_no_python_error``
    If this variable is set to a true value it will prevent Powerline from reporting 
    an error when loaded in a copy of vim without the necessary Python support.

Powerline script overrides
==========================

Powerline script has a number of options controlling powerline behavior. Here 
``VALUE`` always means “some JSON object”.

``-c KEY.NESTED_KEY=VALUE`` or ``--config=KEY.NESTED_KEY=VALUE``
    Overrides options from :file:`powerline/config.json`. 
    ``KEY.KEY2.KEY3=VALUE`` is a shortcut for ``KEY={"KEY2": {"KEY3": VALUE}}``. 
    Multiple options (i.e. ``-c K1=V1 -c K2=V2``) are allowed, result (in the 
    example: ``{"K1": V1, "K2": V2}``) is recursively merged with the contents 
    of the file.

    If ``VALUE`` is omitted then corresponding key will be removed from the 
    configuration (if it was present).

``-t THEME_NAME.KEY.NESTED_KEY=VALUE`` or ``--theme_option=THEME_NAME.KEY.NESTED_KEY=VALUE``
    Overrides options from :file:`powerline/themes/{ext}/{THEME_NAME}.json`. 
    ``KEY.NESTED_KEY=VALUE`` is processed like described above, ``{ext}`` is the 
    first argument to powerline script. May be passed multiple times.

    If ``VALUE`` is omitted then corresponding key will be removed from the 
    configuration (if it was present).

``-p PATH`` or ``--config_path=PATH``
    Sets directory where configuration should be read from. If present, no 
    default locations are searched for configuration. No expansions are 
    performed by powerline script itself, but ``-p ~/.powerline`` will likely be 
    expanded by the shell to something like ``-p /home/user/.powerline``.

Zsh/zpython overrides
=====================

Here overrides are controlled by similarly to the powerline script, but values 
are taken from zsh variables.

``POWERLINE_CONFIG``
    Overrides options from :file:`powerline/config.json`. Should be a zsh 
    associative array with keys equal to ``KEY.NESTED_KEY`` and values being 
    JSON strings. Pair ``KEY.KEY1 VALUE`` is equivalent to ``{"KEY": {"KEY1": 
    VALUE}}``. All pairs are then recursively merged into one dictionary and 
    this dictionary is recursively merged with the contents of the file.

``POWERLINE_THEME_CONFIG``
    Overrides options from :file:`powerline/themes/shell/*.json`. Should be 
    a zsh associative array with keys equal to ``THEME_NAME.KEY.NESTED_KEY`` and 
    values being JSON strings. Is processed like the above ``POWERLINE_CONFIG``, 
    but only subdictionaries for ``THEME_NAME`` key are merged with theme 
    configuration when theme with given name is requested.

``POWERLINE_CONFIG_PATHS``
    Sets directories where configuration should be read from. If present, no 
    default locations are searched for configuration. No expansions are 
    performed by powerline script itself, but zsh usually performs them on its 
    own if you set variable without quotes: ``POWERLINE_CONFIG_PATHS=( ~/example 
    )``. You should use array parameter or the usual colon-separated 
    ``POWERLINE_CONFIG_PATHS=$HOME/path1:$HOME/path2``.

Ipython overrides
=================

Ipython overrides depend on ipython version. Before ipython-0.11 you should pass 
additional keyword arguments to setup() function. After ipython-0.11 you should 
use ``c.Powerline.KEY``. Supported ``KEY`` strings or keyword argument names:

``config_overrides``
    Overrides options from :file:`powerline/config.json`. Should be a dictionary 
    that will be recursively merged with the contents of the file.

``theme_overrides``
    Overrides options from :file:`powerline/themes/ipython/*.json`. Should be 
    a dictionary where keys are theme names and values are dictionaries which 
    will be recursively merged with the contents of the given theme.

``paths``
    Sets directories where configuration should be read from. If present, no 
    default locations are searched for configuration. No expansions are 
    performed thus you cannot use paths starting with ``~/``.

Prompt command
==============

In addition to the above configuration options you can use 
``$POWERLINE_COMMAND`` environment variable to tell shell or tmux to use 
specific powerline implementation and ``$POWERLINE_CONFIG`` to tell zsh or tmux 
where ``powerline-config`` script is located. This is mostly useful for putting 
powerline into different directory.

.. note::

    ``$POWERLINE_COMMAND`` appears in shell scripts without quotes thus you can 
    specify additional parameters in bash. In tmux it is passed to ``eval`` and 
    depends on the shell used. POSIX-compatible shells, zsh, bash and fish will 
    split this variable in this case.

If you want to disable prompt in shell, but still have tmux support or if you 
want to disable tmux support you can use variables 
``$POWERLINE_NO_{SHELL}_PROMPT``/``$POWERLINE_NO_SHELL_PROMPT`` and 
``$POWERLINE_NO_{SHELL}_TMUX_SUPPORT``/``$POWERLINE_NO_SHELL_TMUX_SUPPORT`` 
(substitute ``{SHELL}`` with the name of the shell (all-caps) you want to 
disable support for (e.g. ``BASH``) or use all-inclusive ``SHELL`` that will 
disable support for all shells). These variables have no effect after 
configuration script was sourced (in fish case: after ``powerline-setup`` 
function was run). To disable specific feature support set one of these 
variables to some non-empty value.

If you do not want to disable prompt in shell, but yet do not want to launch 
python twice to get :ref:`above <config-themes-above>` lines you do not use in 
tcsh you should set ``$POWERLINE_NO_TCSH_ABOVE`` or 
``$POWERLINE_NO_SHELL_ABOVE`` variable.

If you do not want to see additional space which is added to the right prompt in 
fish in order to support multiline prompt you should set 
``$POWERLINE_NO_FISH_ABOVE`` or ``$POWERLINE_NO_SHELL_ABOVE`` variables.
