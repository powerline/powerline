***********************
Configuration reference
***********************

.. _config-main:

Main configuration
==================

:Location: :file:`powerline/config.json`

The main configuration file defines some common options that applies to all 
extensions, as well as some extension-specific options like themes and 
colorschemes.

Common configuration
--------------------

Common configuration is a subdictionary that is a value of ``common`` key in 
:file:`powerline/config.json` file.

.. _config-common-term_truecolor:

``term_truecolor``
    Defines whether to output cterm indices (8-bit) or RGB colors (24-bit) 
    to the terminal emulator. See the :ref:`term-feature-support-matrix` for 
    information on whether used terminal emulator supports 24-bit colors.

    This variable is forced to be ``false`` if :ref:`term_escape_style 
    <config-common-term_escape_style>` option is set to ``"fbterm"`` or if it is 
    set to ``"auto"`` and powerline detected fbterm.

.. _config-common-term_escape_style:

``term_escape_style``
    Defines what escapes sequences should be used. Accepts three variants:

    =======  ===================================================================
    Variant  Description
    =======  ===================================================================
    auto     ``xterm`` or ``fbterm`` depending on ``$TERM`` variable value: 
             ``TERM=fbterm`` implies ``fbterm`` escaping style, all other values 
             select ``xterm`` escaping.
    xterm    Uses ``\e[{fb};5;{color}m`` for colors (``{fb}`` is either ``38`` 
             (foreground) or ``48`` (background)). Should be used for most 
             terminals.
    fbterm   Uses ``\e[{fb};{color}}`` for colors (``{fb}`` is either ``1`` 
             (foreground) or ``2`` (background)). Should be used for fbterm: 
             framebuffer terminal.
    =======  ===================================================================

.. _config-common-ambiwidth:

``ambiwidth``
    Tells powerline what to do with characters with East Asian Width Class 
    Ambigious (such as Euro, Registered Sign, Copyright Sign, Greek
    letters, Cyrillic letters). Valid values: any positive integer; it is 
    suggested that this option is only set it to 1 (default) or 2.

.. _config-common-watcher:

``watcher``
    Select filesystem watcher. Variants are

    =======  ===================================
    Variant  Description
    =======  ===================================
    auto     Selects most performant watcher.
    inotify  Select inotify watcher. Linux only.
    stat     Select stat-based polling watcher.
    uv       Select libuv-based watcher.
    =======  ===================================

    Default is ``auto``.

.. _config-common-additional_escapes:

``additional_escapes``
    Valid for shell extensions, makes sense only if :ref:`term_truecolor 
    <config-common-term_truecolor>` is enabled. Is to be set from command-line. 
    Controls additional escaping that is needed for tmux/screen to work with 
    terminal true color escape codes: normally tmux/screen prevent terminal 
    emulator from receiving these control codes thus rendering powerline prompt 
    colorless. Valid values: ``"tmux"``, ``"screen"``, ``null`` (default).

.. _config-common-paths:

``paths``
    Defines additional paths which will be searched for modules when using 
    :ref:`function segment option <config-themes-seg-function>` or :ref:`Vim 
    local_themes option <config-ext-local_themes>`. Paths defined here have 
    priority when searching for modules.

.. _config-common-log:

``log_file``
    Defines path which will hold powerline logs. If not present, logging will be 
    done to stderr.

.. _config-common-log_level:

``log_level``
    String, determines logging level. Defaults to ``WARNING``.

``log_format``
    String, determines format of the log messages. Defaults to 
    ``'%(asctime)s:%(level)s:%(message)s'``.

``interval``
    Number, determines time (in seconds) between checks for changed 
    configuration. Checks are done in a seprate thread. Use ``null`` to check 
    for configuration changes on ``.render()`` call in main thread.
    Defaults to ``None``.

``reload_config``
    Boolean, determines whether configuration should be reloaded at all. 
    Defaults to ``True``.

.. _config-common-default_top_theme:

``default_top_theme``
    String, determines which top-level theme will be used as the default. 
    Defaults to ``powerline`` in unicode locales and ``ascii`` in non-unicode 
    locales. See `Themes`_ section for more details.

Extension-specific configuration
--------------------------------

Common configuration is a subdictionary that is a value of ``ext`` key in 
:file:`powerline/config.json` file.

``colorscheme``
    Defines the colorscheme used for this extension.

.. _config-ext-theme:

``theme``
    Defines the theme used for this extension.

.. _config-ext-top_theme:

``top_theme``
    Defines the top-level theme used for this extension. See `Themes`_ section 
    for more details.

.. _config-ext-local_themes:

``local_themes``
    Defines themes used when certain conditions are met, e.g. for 
    buffer-specific statuslines in vim. Value depends on extension used. For vim 
    it is a dictionary ``{matcher_name : theme_name}``, where ``matcher_name`` 
    is either ``matcher_module.module_attribute`` or ``module_attribute`` 
    (``matcher_module`` defaults to ``powerline.matchers.vim``) and 
    ``module_attribute`` should point to a function that returns boolean value 
    indicating that current buffer has (not) matched conditions. There is an 
    exception for ``matcher_name`` though: if it is ``__tabline__`` no functions 
    are loaded. This special theme is used for ``tabline`` Vim option.

    For shell and ipython it is a simple ``{prompt_type : theme_name}``, where 
    ``prompt_type`` is a string with no special meaning (specifically it does 
    not refer to any Python function). Shell has ``continuation``, and 
    ``select`` prompts with rather self-explanatory names, IPython has ``in2``, 
    ``out`` and ``rewrite`` prompts (refer to IPython documentation for more 
    details) while ``in`` prompt is the default.

``components``
    Determines which extension components should be enabled. This key is highly 
    extension-specific, here is the table of extensions and corresponding 
    components:

    +---------+----------+-----------------------------------------------------+
    |Extension|Component |Description                                          |
    +---------+----------+-----------------------------------------------------+
    |vim      |statusline|Makes Vim use powerline statusline.                  |
    |         +----------+-----------------------------------------------------+
    |         |tabline   |Makes Vim use powerline tabline.                     |
    +---------+----------+-----------------------------------------------------+
    |shell    |prompt    |Makes shell display powerline prompt.                |
    |         +----------+-----------------------------------------------------+
    |         |tmux      |Makes shell report its current working directory     |
    |         |          |and screen width to tmux for tmux powerline          |
    |         |          |bindings.                                            |
    |         |          |                                                     |
    +---------+----------+-----------------------------------------------------+

    All components are enabled by default.

.. _config-colors:

Color definitions
=================

:Location: :file:`powerline/colors.json`

.. _config-colors-colors:

``colors``
    Color definitions, consisting of a dict where the key is the name of the 
    color, and the value is one of the following:

    * A cterm color index.
    * A list with a cterm color index and a hex color string (e.g. ``[123, 
      "aabbcc"]``). This is useful for colorschemes that use colors that 
      aren’t available in color terminals.

``gradients``
    Gradient definitions, consisting of a dict where the key is the name of the 
    gradient, and the value is a list containing one or two items, second item 
    is optional:

    * A list of cterm color indicies.
    * A list of hex color strings.

    It is expected that gradients are defined from least alert color to most 
    alert or non-alert colors are used.

.. _config-colorschemes:

Colorschemes
============

:Location: :file:`powerline/colorschemes/{name}.json`, 
           :file:`powerline/colorschemes/__main__.json`, 
           :file:`powerline/colorschemes/{extension}/{name}.json`

Colorscheme files are processed in order given: definitions from each next file 
override those from each previous file. It is required that either 
:file:`powerline/colorschemes/{name}.json`, or 
:file:`powerline/colorschemes/{extension}/{name}.json` exists.

``name``
    Name of the colorscheme.

.. _config-colorschemes-groups:

``groups``
    Segment highlighting groups, consisting of a dict where the key is the 
    name of the highlighting group (usually the function name for function 
    segments), and the value is either

    #) a dict that defines the foreground color, background color and 
       attributes:

       ``fg``
           Foreground color. Must be defined in :ref:`colors 
           <config-colors-colors>`.

       ``bg``
           Background color. Must be defined in :ref:`colors 
           <config-colors-colors>`.

       ``attrs``
           List of attributes. Valid values are one or more of ``bold``, 
           ``italic`` and ``underline``. Note that some attributes may be 
           unavailable in some applications or terminal emulators. If no 
           attributes are needed this list should be left empty.

    #) a string (an alias): a name of existing group. This group’s definition 
       will be used when this color is requested.

``mode_translations``
    Mode-specific highlighting for extensions that support it (e.g. the vim 
    extension). It’s an easy way of changing a color in a specific mode.  
    Consists of a dict where the key is the mode and the value is a dict 
    with the following options:

    ``colors``
        A dict where the key is the color to be translated in this mode, and 
        the value is the new color. Both the key and the value must be defined 
        in :ref:`colors <config-colors-colors>`.

    ``groups``
        Segment highlighting groups for this mode. Same syntax as the main 
        :ref:`groups <config-colorschemes-groups>` option.

.. _config-themes:

Themes
======

:Location: :file:`powerline/themes/{top_theme}.json`, 
           :file:`powerline/themes/{extension}/__main__.json`, 
           :file:`powerline/themes/{extension}/{name}.json`

Theme files are processed in order given: definitions from each next file 
override those from each previous file. It is required that file 
:file:`powerline/themes/{extension}/{name}.json` exists.

`{top_theme}` component of the file name is obtained either from :ref:`top_theme 
extension-specific key <config-ext-top_theme>` or from :ref:`default_top_theme 
common configuration key <config-common-default_top_theme>`. Powerline ships 
with the following top themes:

.. _config-top_themes-list:

==========================  ====================================================
Theme                       Description
==========================  ====================================================
powerline                   Default powerline theme with fancy powerline symbols
powerline_unicode7          Theme with powerline dividers and unicode-7 symbols
unicode                     Theme without any symbols from private use area
unicode_terminus            Theme containing only symbols from terminus PCF font
unicode_terminus_condensed  Like above, but occupies as less space as possible
ascii                       Theme without any unicode characters at all
==========================  ====================================================

``name``
    Name of the theme.

.. _config-themes-default_module:

``default_module``
    Python module where segments will be looked by default. Defaults to 
    ``powerline.segments.{ext}``.

``spaces``
    Defines number of spaces just before the divider (on the right side) or just 
    after it (on the left side). These spaces will not be added if divider is 
    not drawn.

``use_non_breaking_spaces``
    Determines whether non-breaking spaces should be used in place of the 
    regular ones. This option is needed because regular spaces are not displayed 
    properly when using powerline with some font configuration. Defaults to 
    ``True``.

    .. note::
       Unlike all other options this one is only checked once at startup using 
       whatever theme is :ref:`the default <config-ext-theme>`. If this option 
       is set in the local themes it will be ignored. This option may also be 
       ignored in some bindings.


``dividers``
    Defines the dividers used in all Powerline extensions.

    The ``hard`` dividers are used to divide segments with different 
    background colors, while the ``soft`` dividers are used to divide 
    segments with the same background color.

.. _config-themes-cursor_space:

``cursor_space``
    Space reserved for user input in shell bindings. It is measured in per 
    cents.

``cursor_columns``
    Space reserved for user input in shell bindings. Unlike :ref:`cursor_space 
    <config-themes-cursor_space>` it is measured in absolute amout of columns.

.. _config-themes-segment_data:

``segment_data``
    A dict where keys are segment names or strings ``{module}.{function}``. Used 
    to specify default values for various keys:
    :ref:`after <config-themes-seg-after>`,
    :ref:`before <config-themes-seg-before>`,
    :ref:`contents <config-themes-seg-contents>` (only for string segments
    if :ref:`name <config-themes-seg-name>` is defined),
    :ref:`display <config-themes-seg-display>`.

    Key :ref:`args <config-themes-seg-args>` (only for function and 
    segments_list segments) is handled specially: unlike other values it is 
    merged with all other values, except that a single ``{module}.{function}`` 
    key if found prevents merging all ``{function}`` values.

    When using :ref:`local themes <config-ext-local_themes>` values of these 
    keys are first searched in the segment description, then in ``segment_data`` 
    key of a local theme, then in ``segment_data`` key of a :ref:`default theme 
    <config-ext-theme>`. For the :ref:`default theme <config-ext-theme>` itself 
    step 2 is obviously avoided.

    .. note:: Top-level themes are out of equation here: they are merged
        before the above merging process happens.

.. _config-themes-segments:

``segments``
    A dict with a ``left`` and a ``right`` lists, consisting of segment 
    dictionaries. Shell themes may also contain ``above`` list of dictionaries. 
    Each item in ``above`` list may have ``left`` and ``right`` keys like this 
    dictionary, but no ``above`` key.

    .. _config-themes-above:

    ``above`` list is used for multiline shell configurations.

    ``left`` and ``right`` lists are used for segments that should be put on the 
    left or right side in the output. Actual mechanizm of putting segments on 
    the left or the right depends on used renderer, but most renderers require 
    one to specify segment with :ref:`width <config-themes-seg-width>` ``auto`` 
    on either side to make generated line fill all of the available width.

    Each segment dictionary has the following options:

    .. _config-themes-seg-type:

    ``type``
        The segment type. Can be one of ``function`` (default), ``string`` or 
        ``segments_list``:

        ``function``
            The segment contents is the return value of the function defined in 
            the :ref:`function option <config-themes-seg-function>`.

            List of function segments is available in :ref:`Segment reference 
            <config-segments>` section.

        ``string``
            A static string segment where the contents is defined in the 
            :ref:`contents option <config-themes-seg-contents>`, and the 
            highlighting group is defined in the :ref:`highlight_groups option 
            <config-themes-seg-highlight_groups>`.

        ``segments_list``
            Sub-list of segments. This list only allows :ref:`function 
            <config-themes-seg-function>`, :ref:`segments 
            <config-themes-seg-segments>` and :ref:`args 
            <config-themes-seg-args>` options.

            List of lister segments is available in :ref:`Lister reference 
            <config-listers>` section.

    .. _config-themes-seg-name:

    ``name``
        Segment name. If present allows referring to this segment in 
        :ref:`segment_data <config-themes-segment_data>` dictionary by this 
        name. If not ``string`` segments may not be referred there at all and 
        ``function`` and ``segments_list`` segments may be referred there using 
        either ``{module}.{function_name}`` or ``{function_name}``, whichever 
        will be found first. Function name is taken from :ref:`function key 
        <config-themes-seg-function>`.

        .. note::
            If present prevents ``function`` key from acting as a segment name.

    .. _config-themes-seg-function:

    ``function``
        Function used to get segment contents, in format ``{module}.{function}`` 
        or ``{function}``. If ``{module}`` is omitted :ref:`default_module 
        option <config-themes-default_module>` is used.

    .. _config-themes-seg-highlight_groups:

    ``highlight_groups``
        Highlighting group for this segment. Consists of a prioritized list of 
        highlighting groups, where the first highlighting group that is 
        available in the colorscheme is used.

        Ignored for segments that have ``function`` type.

    .. _config-themes-seg-before:

    ``before``
        A string which will be prepended to the segment contents.

    .. _config-themes-seg-after:

    ``after``
        A string which will be appended to the segment contents.

    .. _config-themes-seg-contents:

    ``contents``
        Segment contents, only required for ``string`` segments.

    .. _config-themes-seg-args:

    ``args``
        A dict of arguments to be passed to a ``function`` segment.

    .. _config-themes-seg-align:

    ``align``
        Aligns the segments contents to the left (``l``), center (``c``) or 
        right (``r``). Has no sense if ``width`` key was not specified or if 
        segment provides its own function for ``auto`` ``width`` handling and 
        does not care about this option.

    .. _config-themes-seg-width:

    ``width``
        Enforces a specific width for this segment.

        This segment will work as a spacer if the width is set to ``auto``.
        Several spacers may be used, and the space will be distributed 
        equally among all the spacer segments. Spacers may have contents, 
        either returned by a function or a static string, and the contents 
        can be aligned with the ``align`` property.

    .. _config-themes-seg-priority:

    ``priority``
        Optional segment priority. Segments with priority ``None`` (the default 
        priority, represented by ``null`` in json) will always be included, 
        regardless of the width of the prompt/statusline.

        If the priority is any number, the segment may be removed if the 
        prompt/statusline width is too small for all the segments to be 
        rendered. A lower number means that the segment has a higher priority.

        Segments are removed according to their priority, with low priority 
        segments being removed first.

    .. _config-themes-seg-draw_divider:

    ``draw_hard_divider``, ``draw_soft_divider``
        Whether to draw a divider between this and the adjacent segment. The 
        adjacent segment is to the *right* for segments on the *left* side, and 
        vice versa. Hard dividers are used between segments with different 
        background colors, soft ones are used between segments with same 
        background. Both options default to ``True``.

    .. _config-themes-seg-draw_inner_divider:

    ``draw_inner_divider``
        Determines whether inner soft dividers are to be drawn for function 
        segments. Only applicable for functions returning multiple segments. 
        Defaults to ``False``.

    .. _config-themes-seg-exclude_modes:

    ``exclude_modes``, ``include_modes``
        A list of modes where this segment will be excluded: the segment is not 
        included or is included in all modes, *except* for the modes in one of 
        these lists respectively. If ``exclude_modes`` is not present then it 
        acts like an empty list (segment is not excluded from any modes). 
        Without ``include_modes`` it acts like a list with all possible modes 
        (segment is included in all modes). When there are both 
        ``exclude_modes`` overrides ``include_modes``.

    .. _config-themes-seg-exclude_function:

    ``exclude_function``, ``include_function``
        Function name in a form ``{name}`` or ``{module}.{name}`` (in the first 
        form ``{module}`` defaults to ``powerline.selectors.{ext}``). Determines 
        under which condition specific segment will be included or excluded. By 
        default segment is always included and never excluded. 
        ``exclude_function`` overrides ``include_function``.

        .. note::
            Options :ref:`exclude_/include_modes 
            <config-themes-seg-exclude_modes>` complement 
            ``exclude_/include_functions``: segment will be included if it is 
            included by either ``include_mode`` or ``include_function`` and will 
            be excluded if it is excluded by either ``exclude_mode`` or 
            ``exclude_function``.

    .. _config-themes-seg-display:

    ``display``
        Boolean. If false disables displaying of the segment.
        Defaults to ``True``.

    .. _config-themes-seg-segments:

    ``segments``
        A list of subsegments.
