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

``g:powerline_theme_overrides``
    Dictionary mapping theme names to theme overrides, recursively merged with 
    contents of :file:`powerline/themes/vim/{key}.json`. Note that this way some 
    value (e.g. segment) in a list cannot be redefined, only the whole list 
    itself: only dictionaries are merged recursively.

``g:powerline_config_paths``
    Paths list (each path must be expanded, ``~`` shortcut is not supported). 
    Points to the list of directories which will be searched for configuration. 
    When this option is present, none of the other locations are searched.

``g:powerline_no_python_error``
    If this variable is set to a true value it will prevent Powerline from reporting 
    an error when loaded in a copy of vim without the necessary Python support.

``g:powerline_use_var_handler``
    This variable may be set to either 0 or 1. If it is set to 1 then Vim will 
    save log in ``g:powerline_log_messages`` variable in addition to whatever 
    was configured in :ref:`log_* options <config-common-log>`. Level is always 
    :ref:`log_level <config-common-log_level>`, same for format.

.. _local-configuration-overrides-script:

Powerline script overrides
==========================

Powerline script has a number of options controlling powerline behavior. Here 
``VALUE`` always means “some JSON object”.

``-c KEY.NESTED_KEY=VALUE`` or ``--config-override=KEY.NESTED_KEY=VALUE``
    Overrides options from :file:`powerline/config.json`. 
    ``KEY.KEY2.KEY3=VALUE`` is a shortcut for ``KEY={"KEY2": {"KEY3": VALUE}}``. 
    Multiple options (i.e. ``-c K1=V1 -c K2=V2``) are allowed, result (in the 
    example: ``{"K1": V1, "K2": V2}``) is recursively merged with the contents 
    of the file.

    If ``VALUE`` is omitted then corresponding key will be removed from the 
    configuration (if it was present).

``-t THEME_NAME.KEY.NESTED_KEY=VALUE`` or ``--theme-override=THEME_NAME.KEY.NESTED_KEY=VALUE``
    Overrides options from :file:`powerline/themes/{ext}/{THEME_NAME}.json`. 
    ``KEY.NESTED_KEY=VALUE`` is processed like described above, ``{ext}`` is the 
    first argument to powerline script. May be passed multiple times.

    If ``VALUE`` is omitted then corresponding key will be removed from the 
    configuration (if it was present).

``-p PATH`` or ``--config-path=PATH``
    Sets directory where configuration should be read from. If present, no 
    default locations are searched for configuration. No expansions are 
    performed by powerline script itself, but ``-p ~/.powerline`` will likely be 
    expanded by the shell to something like ``-p /home/user/.powerline``.

.. warning::
    Such overrides are suggested for testing purposes only. Use 
    :ref:`Environment variables overrides <local-configuration-overrides-env>` 
    for other purposes.

.. _local-configuration-overrides-env:

Environment variables overrides
===============================

All bindings that use ``POWERLINE_COMMAND`` environment variable support taking 
overrides from environment variables. In this case overrides should look like 
the following::

    OVERRIDE='key1.key2.key3=value;key4.key5={"value":1};key6=true;key1.key7=10'

. This will be parsed into

.. code-block:: Python

    {
        "key1": {
            "key2": {
                "key3": "value"
            },
            "key7": 10,
        },
        "key4": {
            "key5": {
                "value": 1,
            },
        },
        "key6": True,
    }

. Rules:

#. Environment variable must form a semicolon-separated list of key-value pairs: 
   ``key=value;key2=value2``.
#. Keys are always dot-separated strings that must not contain equals sign (as 
   well as semicolon) or start with an underscore. They are interpreted 
   literally and create a nested set of dictionaries: ``k1.k2.k3`` creates 
   ``{"k1":{"k2":{}}}`` and inside the innermost dictionary last key (``k3`` in 
   the example) is contained with its value.
#. Value may be empty in which case they are interpreted as an order to remove 
   some value: ``k1.k2=`` will form ``{"k1":{"k2":REMOVE_THIS_KEY}}`` nested 
   dictionary where ``k2`` value is a special value that tells 
   dictionary-merging function to remove ``k2`` rather then replace it with 
   something.
#. Value may be a JSON strings like ``{"a":1}`` (JSON dictionary), ``["a",1]`` 
   (JSON list), ``1`` or ``-1`` (JSON number), ``"abc"`` (JSON string) or 
   ``true``, ``false`` and ``null`` (JSON boolean objects and ``Null`` object 
   from JSON). General rule is that anything starting with a digit (U+0030 till 
   U+0039, inclusive), a hyphenminus (U+002D), a quotation mark (U+0022), a left 
   curly bracket (U+007B) or a left square bracket (U+005B) is considered to be 
   some JSON object, same for *exact* values ``true``, ``false`` and ``null``.
#. Any other value is considered to be literal string: ``k1=foo:bar`` parses to 
   ``{"k1": "foo:bar"}``.

The following environment variables may be used for overrides according to the 
above rules:

``POWERLINE_CONFIG_OVERRIDES``
    Overrides values from :file:`powerline/config.json`.

``POWERLINE_THEME_OVERRIDES``
    Overrides values from :file:`powerline/themes/{ext}/{key}.json`. Top-level 
    key is treated as a name of the theme for which overrides are used: e.g. to 
    disable cwd segment defined in :file:`powerline/themes/shell/default.json` 
    one needs to use::

        POWERLINE_THEME_OVERRIDES=default.segment_data.cwd.display=false

Additionally one environment variable is a usual *colon*-separated list of 
directories: ``POWERLINE_CONFIG_PATHS``. This one defines paths which will be 
searched for configuration. Empty paths in ``POWERLINE_CONFIG_PATHS`` are 
ignored.

.. note::
    Overrides from environment variables have lower priority then 
    :ref:`Powerline script overrides <local-configuration-overrides-script>`. 
    Latter are suggested for tests only.

Zsh/zpython overrides
=====================

Here overrides are controlled by similarly to the powerline script, but values 
are taken from zsh variables. :ref:`Environment variable overrides 
<local-configuration-overrides-env>` are also supported: if variable is a string 
this variant is used.

``POWERLINE_CONFIG_OVERRIDES``
    Overrides options from :file:`powerline/config.json`. Should be a zsh 
    associative array with keys equal to ``KEY.NESTED_KEY`` and values being 
    JSON strings. Pair ``KEY.KEY1 VALUE`` is equivalent to ``{"KEY": {"KEY1": 
    VALUE}}``. All pairs are then recursively merged into one dictionary and 
    this dictionary is recursively merged with the contents of the file.

``POWERLINE_THEME_OVERRIDES``
    Overrides options from :file:`powerline/themes/shell/*.json`. Should be 
    a zsh associative array with keys equal to ``THEME_NAME.KEY.NESTED_KEY`` and 
    values being JSON strings. Is processed like the above 
    ``POWERLINE_CONFIG_OVERRIDES``, but only subdictionaries for ``THEME_NAME`` 
    key are merged with theme configuration when theme with given name is 
    requested.

``POWERLINE_CONFIG_PATHS``
    Sets directories where configuration should be read from. If present, no 
    default locations are searched for configuration. No expansions are 
    performed by powerline script itself, but zsh usually performs them on its 
    own if variable without is set without quotes: ``POWERLINE_CONFIG_PATHS=( 
    ~/example )``. In addition to arrays usual colon-separated “array” string 
    can be used: ``POWERLINE_CONFIG_PATHS=$HOME/path1:$HOME/path2``.

Ipython overrides
=================

Ipython overrides depend on ipython version. Before ipython-0.11 additional 
keyword arguments should be passed to setup() function. After ipython-0.11 
``c.Powerline.KEY`` should be used. Supported ``KEY`` strings or keyword 
argument names:

``config_overrides``
    Overrides options from :file:`powerline/config.json`. Should be a dictionary 
    that will be recursively merged with the contents of the file.

``theme_overrides``
    Overrides options from :file:`powerline/themes/ipython/*.json`. Should be 
    a dictionary where keys are theme names and values are dictionaries which 
    will be recursively merged with the contents of the given theme.

``config_paths``
    Sets directories where configuration should be read from. If present, no 
    default locations are searched for configuration. No expansions are 
    performed thus paths starting with ``~/`` cannot be used: use 
    :py:func:`os.path.expanduser`.

Prompt command
==============

In addition to the above configuration options ``$POWERLINE_COMMAND`` 
environment variable can be used to tell shell or tmux to use specific powerline 
implementation and ``$POWERLINE_CONFIG_COMMAND`` to tell zsh or tmux where 
``powerline-config`` script is located. This is mostly useful for putting 
powerline into different directory.

.. note::

    ``$POWERLINE_COMMAND`` is always treated as one path in shell bindings, so 
    path with spaces in it may be used. To specify additional arguments one may 
    use ``$POWERLINE_COMMAND_ARGS``, but note that this variable exists for 
    testing purposes only and may be removed. One should use :ref:`Environment 
    variable overrides <local-configuration-overrides-env>` instead.

To disable prompt in shell, but still have tmux support or to disable tmux 
support environment variables ``$POWERLINE_NO_{SHELL}_PROMPT`` and 
``$POWERLINE_NO_{SHELL}_TMUX_SUPPORT`` can be used (substitute ``{SHELL}`` with 
the name of the shell (all-caps) that should be affected (e.g. ``BASH``) or use 
all-inclusive ``SHELL`` that will disable support for all shells). These 
variables have no effect after configuration script was sourced (in fish case: 
after ``powerline-setup`` function was run). To disable specific feature support 
set one of these variables to some non-empty value.

In order to keep shell prompt, but avoid launching Python twice to get unused 
:ref:`above <config-themes-above>` lines in tcsh ``$POWERLINE_NO_TCSH_ABOVE`` or 
``$POWERLINE_NO_SHELL_ABOVE`` variable should be set.

In order to remove additional space from the end of the right prompt in fish 
that was added in order to support multiline prompt ``$POWERLINE_NO_FISH_ABOVE`` 
or ``$POWERLINE_NO_SHELL_ABOVE`` variable should be set.

PDB overrides
=============

Like shell bindings :ref:`PDB bindings <pdb-prompt>` take overrides from 
:ref:`environment variables <local-configuration-overrides-env>`.
