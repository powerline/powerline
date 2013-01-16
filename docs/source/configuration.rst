Configuration
=============

Powerline is configured with one main configuration file, and with separate 
configuration files for themes and colorschemes. All configuration files are 
written in JSON, with the exception of segment definitions, which are 
written in Python.

Powerline provides default configurations in the following locations:

`Main configuration`_
    :file:`powerline/config.json`
`Colorschemes`_
    :file:`powerline/colorschemes/default.json`
`Themes`_
    :file:`powerline/themes/{extension}/default.json`

The default configuration files are stored in the main package. User 
configuration files are stored in :file:`$XDG_CONFIG_HOME/powerline` for 
Linux users, and in :file:`~/.config/powerline` for OS X users. This usually 
corresponds to :file:`~/.config/powerline` on both platforms.

The easiest way of creating your own version of any configuration file is to 
copy the configuration file from the main package to the corresponding path 
in your user-specific config directory and make your changes to the new 
file. Example:

.. code-block:: sh

    $ cp /path/to/powerline/colorschemes/default.json \
        ~/.config/powerline/colorschemes/mycolorscheme.json

    $ vim ~/.config/powerline/colorschemes/mycolorscheme.json

.. note:: If you're creating a custom colorscheme or theme, remember to 
   rename it and update your main configuration to use the new 
   colorscheme/theme!

Main configuration
------------------

:Location: :file:`powerline/config.json`

The main configuration file defines some common options that applies to all 
extensions, as well as some extension-specific options like themes and 
colorschemes.

Common configuration
^^^^^^^^^^^^^^^^^^^^

``dividers``
    Defines the dividers used in all Powerline extensions. This option 
    should usually only be changed if you don't have a patched font, or if 
    you use a font patched with the legacy font patcher.

    The ``hard`` dividers are used to divide segments with different 
    background colors, while the ``soft`` dividers are used to divide 
    segments with the same background color.

Extension-specific configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

``colorscheme``
    Defines the colorscheme used for this extension.

``theme``
    Defines the theme used for this extension.

``local_themes``
    Defines themes used when certain conditions are met, e.g. for 
    buffer-specific statuslines in vim. Requires a custom matcher and theme.

Colorschemes
------------

:Location: :file:`powerline/colorschemes/{extension}/{name}.json`

``name``
    Name of the colorscheme.

``colors``
    .. _config-colorscheme-colors:

    Color definitions, consisting of a dict where the key is the name of the 
    color, and the value is one of the following:

    * A cterm color index.
    * A list of two integers, where the first integer is a cterm color 
      index, and the second is an RGB/hex color. This is useful for 
      colorschemes that use colors that aren't available in color terminals.

``groups``
    .. _config-colorscheme-groups:

    Segment highlighting groups, consisting of a dict where the key is the 
    name of the highlighting group (usually the function name for function 
    segments), and the value is a dict that defines the foreground color, 
    background color and optional attributes:

    ``fg``
        Foreground color. Must be defined in :ref:`colors 
        <config-colorscheme-colors>`.

    ``bg``
        Background color. Must be defined in :ref:`colors 
        <config-colorscheme-colors>`.

    ``attr``
        Optional list of attributes. Valid values are one or more of 
        ``bold``, ``italic`` and ``underline``. Note that some attributes 
        may be unavailable in some applications or terminal emulators.

``mode_translations``
    Mode-specific highlighting for extensions that support it (e.g. the vim 
    extension). It's an easy way of changing a color in a specific mode.  
    Consists of a dict where the key is the mode and the value is a dict 
    with the following options:

    ``colors``
        A dict where the key is the color to be translated in this mode, and 
        the value is the new color. Both the key and the value must be 
        defined in :ref:`colors <config-colorscheme-colors>`.

    ``groups``
        Segment highlighting groups for this mode. Same syntax as the main 
        :ref:`groups <config-colorscheme-groups>` option.

Themes
------

:Location: :file:`powerline/themes/{extension}/{name}.json`

``name``
    Name of the theme.

``segments``
    A dict with a ``left`` and a ``right`` list, consisting of segment 
    dicts. Each segment has the following options:

    ``type``
        The segment type. Can be one of ``function`` (default), ``string`` 
        or ``filler``:

        ``function``
            The segment contents is the return value of the function defined 
            in the :ref:`name option <config-themes-seg-name>`.

        ``string``
            A static string segment where the contents is defined in the 
            :ref:`contents option <config-themes-seg-contents>`, and the 
            highlighting group is defined in the :ref:`highlight option 
            <config-themes-seg-highlight>`.

        ``filler``
            If the statusline is rendered with a specific width, remaining 
            whitespace is distributed among filler segments. The 
            highlighting group is defined in the :ref:`highlight option 
            <config-themes-seg-highlight>`.

    ``module``
        .. _config-themes-seg-module:

        Function module, only required for function segments. Defaults to 
        ``core``.

    ``name``
        .. _config-themes-seg-name:

        Function name, only required for function segments.

    ``highlight``
        .. _config-themes-seg-highlight:

        Highlighting group for this segment. Consists of a prioritized list 
        of highlighting groups, where the first highlighting group that is 
        available in the colorscheme is used.

    ``before``
        A string which will be prepended to the segment contents.

    ``after``
        A string which will be appended to the segment contents.

    ``contents``
        .. _config-themes-seg-contents:

        Segment contents, only required for ``string`` segments.

    ``args``
        A dict of arguments to be passed to a ``function`` segment.

    ``ljust``
        If set, the segment will be left justified to the width specified by 
        this option.

    ``rjust``
        If set, the segment will be right justified to the width specified 
        by this option.

    ``priority``
        Optional segment priority. Segments with priority ``-1`` (the 
        default priority) will always be included, regardless of the width 
        of the prompt/statusline.

        If the priority is ``0`` or more, the segment may be removed if the 
        prompt/statusline width is too small for all the segments to be 
        rendered. A lower number means that the segment has a higher 
        priority.

        Segments are removed according to their priority, with low priority 
        segments being removed first.

    ``draw_divider``
        Whether to draw a divider between this and the adjacent segment. The 
        adjacent segment is to the *right* for segments on the *left* side, 
        and vice versa.

    ``exclude_modes``
        A list of modes where this segment will be excluded: The segment is 
        included in all modes, *except* for the modes in this list.

    ``include_modes``
        A list of modes where this segment will be included: The segment is 
        *not* included in any modes, *except* for the modes in this list.

Segments
--------

Segments are written in Python, and the default segments provided with 
Powerline are located in 
:file:`powerline/ext/{extension}/segments/{module}.py`. User-defined 
segments can be defined in the corresponding path in the user's config 
directory.

Segments are regular Python functions, and they may accept arguments. All 
arguments should have a default value which will be used for themes that 
don't provide an ``args`` dict.

A segment function must return one of the following values:

* ``None``, which will remove the segment from the prompt/statusline.
* A string, which will be the segment contents.
* A dict consisting of a ``contents`` string, and a ``highlight`` list. This 
  is useful for providing a particular highlighting group depending on the 
  segment contents.
