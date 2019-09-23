# vim:fileencoding=utf-8:noet
import operator

try:
    from __builtin__ import reduce
except ImportError:
    from functools import reduce

from pygments.token import Token
from prompt_toolkit.styles import DynamicStyle

from powerline.renderers.ipython import IPythonRenderer
from powerline.ipython import IPythonInfo
from powerline.colorscheme import ATTR_BOLD, ATTR_ITALIC, ATTR_UNDERLINE

used_styles = []
seen = set()

class PowerlinePromptStyle(DynamicStyle):
    @property
    def style_rules(self):
        return (self.get_style() or self._dummy).style_rules + used_styles

    def invalidation_hash(self):
        return (h + 1 for h in tuple(super(PowerlinePromptStyle, self).invalidation_hash()))


class IPythonPygmentsRenderer(IPythonRenderer):
    reduce_initial = []

    def __init__(self, **kwargs):
        super(IPythonPygmentsRenderer, self).__init__(**kwargs)
        self.character_translations[ord(' ')] = ' '

    def get_segment_info(self, segment_info, mode):
        return super(IPythonPygmentsRenderer, self).get_segment_info(
            IPythonInfo(segment_info), mode)

    @staticmethod
    def hl_join(segments):
        return reduce(operator.iadd, segments, [])

    def hl(self, escaped_contents, fg=None, bg=None, attrs=None, *args, **kwargs):
        '''Output highlighted chunk.

        This implementation outputs a list containing a single pair
        (:py:class:`string`,
        :py:class:`powerline.lib.unicode.unicode`).
        '''
        guifg = None
        guibg = None
        att = []
        if fg is not None and fg is not False:
            guifg = fg[1]
        if bg is not None and bg is not False:
            guibg = bg[1]
        if attrs:
            att = []
            if attrs & ATTR_BOLD:
                att.append('bold')
            if attrs & ATTR_ITALIC:
                att.append('italic')
            if attrs & ATTR_UNDERLINE:
                att.append('underline')

        fg = (('%06x' % guifg) if guifg is not None else '')
        bg = (('%06x' % guibg) if guibg is not None else '')
        name = (
            'pl'
            + ''.join(('_a' + attr for attr in att))
            + '_f' + fg + '_b' + bg
        )

        global seen
        if not (name in seen):
            global used_styles
            used_styles += [('pygments.' + name,
                ''.join((' ' + attr for attr in att))
                + (' fg:#' + fg if fg != '' else ' fg:')
                + (' bg:#' + bg if bg != '' else ' bg:'))]
            seen.add(name)
        return [((name,), escaped_contents)]

    def hlstyle(self, *args, **kwargs):
        return []

    def get_client_id(self, segment_info):
        return id(self)


renderer = IPythonPygmentsRenderer
